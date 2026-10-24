#!/usr/bin/env python3
# impl: FR-001-12
"""Devnet e2e однією командою: dry-run без мережі або live через RPC.

Приклади:
  python3 scripts/run_devnet.py --dry-run --keypair keys/devnet-e2e.json
  python3 scripts/run_devnet.py --live --rpc https://api.devnet.solana.com \\
      --keypair keys/devnet-e2e.json --batches 2

Ключ: JSON-масив з 64 int (формат solders), ТІЛЬКИ devnet.
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from itb import base58, config as C, ed25519, measure
from itb.sender import DirectTpuStub, RpcSender


def rpc_call(rpc_url, method, params, tries=8):
    import time
    import urllib.error
    last = None
    for i in range(tries):
        req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        r = urllib.request.Request(rpc_url, data=json.dumps(req).encode(),
                                   headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                out = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            time.sleep(min(60, 5 * (i + 1)))
            continue
        if out.get("error"):
            last = str(out["error"])
            time.sleep(min(60, 5 * (i + 1)))
            continue
        return out["result"]
    raise RuntimeError(f"RPC {method} failed after {tries}: {last}")


def fetch_block(rpc_url, slot):
    res = rpc_call(rpc_url, "getBlock",
                   [slot, {"encoding": "jsonParsed",
                           "maxSupportedTransactionVersion": 1,
                           "transactionDetails": "full"}])
    if res is None:
        return None
    txs = []
    for t in res.get("transactions", []):
        if isinstance(t, dict) and "signature" in t:
            txs.append({"signature": t["signature"]})
        else:
            inner = (t.get("transaction", {}) or {})
            arr = inner.get("signatures", []) or []
            if arr:
                txs.append({"signature": arr[0]})
    return {"transactions": txs}


def confirm_slots(rpc_url, signatures, timeout_s=180):
    """Чекати підтвердження; повернути {sig: slot}."""
    import time
    pending = list(signatures)
    found = {}
    deadline = time.time() + timeout_s
    while pending and time.time() < deadline:
        res = rpc_call(rpc_url, "getSignatureStatuses",
                       [pending, {"searchTransactionHistory": True}])
        still = []
        for sig, v in zip(pending, res.get("value") or []):
            if v and v.get("slot"):
                found[sig] = v["slot"]
            else:
                still.append(sig)
        pending = still
        if pending:
            time.sleep(4)
    return found, pending


def recollect_with_actual_slots(data_dir, rpc_url):
    """Переписати target_slot за фактичними слотами і перезбирати landed."""
    import csv
    from itb import collector as C
    data_dir = Path(data_dir)
    rows = list(csv.DictReader((data_dir / "sent.csv").open(encoding="utf-8")))
    sigs = [r["signature"] for r in rows]
    found, missing = confirm_slots(rpc_url, sigs)
    print(f"confirmed: {len(found)}, unconfirmed: {len(missing)}")
    slot_of = {s: found.get(s) for s in sigs}
    fixed = [dict(r, target_slot=slot_of[r["signature"]] if slot_of[r["signature"]] else -1)
             for r in rows]
    with (data_dir / "sent.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(fixed)
    landed = data_dir / "landed.csv"
    if landed.is_file():
        landed.unlink()  # прибрати missing-заглушки первинного збору
    C.collect(data_dir, lambda slot: fetch_block(rpc_url, slot) if slot >= 0 else None)
    return found, missing


def load_keypair(path: Path):
    raw = json.loads(Path(path).read_text())
    sk64 = bytes(raw)
    if len(sk64) != 64:
        raise ValueError("keypair має бути 64 int (solders-формат)")
    return sk64


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Devnet e2e: батч вимірювання.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--rpc", default=os.environ.get("RPC_URL", "https://api.devnet.solana.com"))
    ap.add_argument("--keypair", required=True)
    ap.add_argument("--data-dir", default="data-devnet")
    ap.add_argument("--ledger", default="data-devnet/spend_ledger.jsonl")
    ap.add_argument("--arm", default="A")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--batches", type=int, default=1)
    ap.add_argument("--blockhash", default=None, help="hex; у live береться з RPC")
    a = ap.parse_args(argv)
    mode = "live" if a.live else "dry-run"

    cfg = C.load("config/experiment.yaml")
    sk64 = load_keypair(a.keypair)
    pub_b58 = base58.encode(sk64[32:])
    print(f"payer: {pub_b58} (devnet-only ключ)")
    keypairs = {f"payer-pool-{i}": sk64 for i in range(12)}
    keypairs["payer-shared-conflict"] = sk64

    if a.blockhash:
        bh = bytes.fromhex(a.blockhash)
    elif mode == "dry-run":
        raise SystemExit("--dry-run потребує --blockhash (без мережі)")
    else:
        bh_b58 = rpc_call(a.rpc, "getLatestBlockhash",
                          [{"commitment": "confirmed"}])["value"]["blockhash"]
        bh = base58.decode(bh_b58)
        print(f"blockhash: {bh_b58}")
    sender = RpcSender(a.rpc).send if mode == "live" else DirectTpuStub().send
    fetch = (lambda slot: fetch_block(a.rpc, slot) if slot > 0 else None) \
        if mode == "live" else None

    levels = {"A": [0, 500, 1000], "B": [5000], "C": [5000, 100000, 200000],
              "D": [0, 500, 1000]}[a.arm]
    window = {"validator": "devnet-smoke", "label": "devnet-1",
              "start_slot": 0, "end_slot": 0}
    for b in range(a.batches):
        rep = measure.run_batch(cfg, a.arm, a.seed + b, levels, window, bh,
                                keypairs, sender, fetch, mode,
                                a.data_dir, a.ledger, actual_leader="devnet-smoke",
                                batch_seq=b)
        print(f"batch {b}: {rep}")
    if mode == "live":
        found, missing = recollect_with_actual_slots(a.data_dir, a.rpc)
        if missing:
            print(f"не підтверджено: {missing}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
