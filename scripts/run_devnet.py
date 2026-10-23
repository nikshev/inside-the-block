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


def rpc_call(rpc_url, method, params):
    req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = urllib.request.Request(rpc_url, data=json.dumps(req).encode(),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        out = json.loads(resp.read().decode())
    if out.get("error"):
        raise RuntimeError(f"RPC {method}: {out['error']}")
    return out["result"]


def fetch_block(rpc_url, slot):
    res = rpc_call(rpc_url, "getBlock",
                   [slot, {"encoding": "jsonParsed",
                           "maxSupportedTransactionVersion": 0,
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
        bh = base64.b64decode(rpc_call(a.rpc, "getLatestBlockhash",
                                       [{"commitment": "confirmed"}])["value"]["blockhash"])
    sender = RpcSender(a.rpc) if mode == "live" else DirectTpuStub()
    fetch = (lambda slot: fetch_block(a.rpc, slot)) if mode == "live" else None

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
