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


def recollect_with_actual_slots(data_dir, rpc_url, only_sigs=None):
    """Переписати target_slot за фактичними слотами і перезбирати landed.

    only_sigs: збирати лише ці сигнатури (ігнорувати інші рядки sent.csv).
    """
    import csv
    from itb import collector as C
    data_dir = Path(data_dir)
    rows = list(csv.DictReader((data_dir / "sent.csv").open(encoding="utf-8")))
    if only_sigs is not None:
        keep = set(only_sigs)
        rows = [r for r in rows if r["signature"] in keep]
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
    ap.add_argument("--label", default="mainnet-1", help="мітка валідатора/прогону в batch_id")
    ap.add_argument("--burst", action="store_true",
                    help="залп: підписати все, відправити всі поспіль (для концентрації в слоті)")
    ap.add_argument("--attempts", type=int, default=1,
                    help="спроб залпу зі свіжим blockhash (кожна спроба рахується guard)")
    ap.add_argument("--jobs", type=int, default=8,
                    help="паралельних підписів (multiprocessing, stdlib)")
    ap.add_argument("--validator-identity", default=None,
                    help="identity цільового валідатора; без нього — опортуністична відправка")
    ap.add_argument("--no-wait", action="store_true",
                    help="не чекати вікна лідера (тільки для smoke)")
    a = ap.parse_args(argv)
    mode = "live" if a.live else "dry-run"

    cfg = C.load("config/experiment.yaml")
    try:
        import yaml as _yaml
        _raw = _yaml.safe_load(open("config/experiment.yaml", encoding="utf-8"))
    except ImportError:
        _raw = {}
    _arms = (_raw or {}).get("arms", {})
    sk64 = load_keypair(a.keypair)
    pub_b58 = base58.encode(sk64[32:])
    print(f"payer: {pub_b58} (операційний ключ — перевір, що це очікувана адреса)")
    keypairs = {f"payer-pool-{i}": sk64 for i in range(12)}
    keypairs["payer-shared-conflict"] = sk64

    from itb import schedule as S

    def fresh_bh():
        bh_b58 = rpc_call(a.rpc, "getLatestBlockhash",
                          [{"commitment": "confirmed"}])["value"]["blockhash"]
        print(f"blockhash: {bh_b58}")
        return base58.decode(bh_b58)

    if a.blockhash:
        bh = bytes.fromhex(a.blockhash)
    elif mode == "dry-run":
        raise SystemExit("--dry-run потребує --blockhash (без мережі)")
    else:
        bh = fresh_bh()
    sender = RpcSender(a.rpc).send if mode == "live" else DirectTpuStub().send
    fetch = (lambda slot: fetch_block(a.rpc, slot) if slot > 0 else None) \
        if mode == "live" else None

    levels = {"A": _arms.get("A_levels", [0, 500, 1000]),
              "B": [_arms.get("B_price", 5000)],
              "C": [_arms.get("C_price", 5000)] + _arms.get("C_limits", [200000]),
              "D": _arms.get("D_levels", [0, 500, 1000])}[a.arm]
    ident = a.validator_identity or f"{a.label}-opportunistic"
    window = {"validator": ident, "label": a.label,
              "start_slot": 0, "end_slot": 0}
    strategy = "burst" if a.burst else "stream"

    def live_targeted(arm_batch_seq):
        """Підписати заздалегідь → вікно в межах життя blockhash → залп.

        Повертає rep fire_batch. Кидає SystemExit, якщо вікна немає.
        """
        import time
        from itb import measure as M
        last_err = "no-attempt"
        for att in range(max(1, a.attempts)):
            info = rpc_call(a.rpc, "getLatestBlockhash",
                            [{"commitment": "confirmed"}])["value"]
            bh = base58.decode(info["blockhash"])
            # Увага: lastValidBlockHeight — це ВИСОТА, не слот. Дедлайн рахуємо
            # від слота отримання: ~150 слотів життя, запас 20.
            bh_slot = rpc_call(a.rpc, "getSlot", [{"commitment": "confirmed"}])
            prep = M.prepare_batch(cfg, a.arm, a.seed + arm_batch_seq, levels,
                                    window, bh, keypairs, a.data_dir,
                                    batch_seq=arm_batch_seq * 100 + att, jobs=a.jobs,
                                    write_sent=False)
            epoch_info = rpc_call(a.rpc, "getEpochInfo", [{"commitment": "confirmed"}])
            cur_abs = rpc_call(a.rpc, "getSlot", [{"commitment": "confirmed"}])
            if cur_abs >= bh_slot + 130:
                last_err = "blockhash-expired-during-sign"
                continue
            first_slot = cur_abs - epoch_info["slotIndex"]
            sched = rpc_call(a.rpc, "getLeaderSchedule", [])
            if sched is None:
                raise SystemExit("getLeaderSchedule повернув null; спробуй інший RPC")
            wins = S.windows(sched, ident, epoch_info["epoch"])
            cur_rel = cur_abs - first_slot
            latest_start = (bh_slot + 130) - first_slot
            future = [w for w in wins
                      if cur_rel + 2 < w["start_slot"] < latest_start - 5]
            if not future:
                last_err = "no-window-in-bh-lifetime"
                continue
            w = future[0]
            window.update(w)
            for row_prep in prep["signed"]:
                row_prep["target_slot"] = w["start_slot"]
            target_abs = first_slot + w["start_slot"] - 2
            print(f"спроба {att}: вікно rel {w['start_slot']}..{w['end_slot']} "
                  f"(abs {first_slot + w['start_slot']}), чекаю abs {target_abs}...")
            while rpc_call(a.rpc, "getSlot", [{"commitment": "confirmed"}]) < target_abs:
                time.sleep(0.2)
            return M.fire_batch(cfg, prep, sender, fetch, a.data_dir, a.ledger)
        raise SystemExit(f"live_targeted: усі спроби вичерпано ({last_err})")

    fired_sigs: list = []
    for b in range(a.batches):
        if mode == "live" and a.validator_identity and not a.no_wait:
            rep = live_targeted(b)
            print(f"batch {b} (targeted): " +
                  str({k: rep[k] for k in rep if k != "signatures"}))
            fired_sigs.extend(rep.get("signatures", []))
            continue
        for att in range(a.attempts if mode == "live" else 1):
            if mode == "live" and (a.burst or att > 0) and not a.blockhash:
                bh = fresh_bh()
            rep = measure.run_batch(cfg, a.arm, a.seed + b, levels, window, bh,
                                    keypairs, sender, fetch, mode,
                                    a.data_dir, a.ledger, actual_leader=ident,
                                    batch_seq=b * 100 + att, send_strategy=strategy)
            print(f"batch {b} attempt {att}: " +
                  str({k: rep[k] for k in rep if k != "signatures"}))
            fired_sigs.extend(rep.get("signatures", []))
    if mode == "live":
        found, missing = recollect_with_actual_slots(
            a.data_dir, a.rpc, only_sigs=fired_sigs or None)
        leaders = {}
        for sig, slot in found.items():
            try:
                leaders[str(slot)] = rpc_call(
                    a.rpc, "getSlotLeaders", [slot, 1])[0]
            except Exception as e:
                leaders[str(slot)] = f"ERR {e}"[:80]
        with open(Path(a.data_dir) / "leaders.json", "w") as f:
            json.dump({"target": ident, "slots": leaders}, f, indent=2)
        print(f"лідери слотів: {leaders}")
        if missing:
            print(f"не підтверджено: {missing}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
