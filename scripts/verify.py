#!/usr/bin/env python3
# impl: FR-001-08, FR-004-03
"""Перевірка landed.csv проти сирих блоків data/blocks/*.json.

Контракт: specs/001-pipeline-safety/contracts/verify.md (оновлено 004).
Використання:
  python3 scripts/verify.py data/                              # локально
  python3 scripts/verify.py data/ --live-check --rpc URL       # звірка з ланцюгом
"""

import csv
import json
import os
import sys
import urllib.request
from pathlib import Path


def load_block_sigs(data_dir: Path, slot: int):
    """Порядок сигнатур у слоті або None, якщо слот-файлу немає."""
    p = data_dir / "blocks" / f"{slot}.json"
    if not p.is_file():
        return None
    payload = json.loads(p.read_text(encoding="utf-8"))
    block = payload.get("block", payload)
    txs = block.get("transactions", [])
    sigs = []
    for t in txs:
        if isinstance(t, dict):
            sigs.append(t.get("signature"))
        else:
            sigs.append(t)
    return sigs


def verify(data_dir: Path) -> list:
    """Повертає список розбіжностей; друкує таблицю signature→slot→position."""
    mismatches = []
    with (data_dir / "landed.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            sig, slot = row["signature"], int(row["slot"])
            want_pos = int(row["position"])
            status = row.get("status", "landed")
            sigs = load_block_sigs(data_dir, slot)
            if status == "missing":
                if sigs is not None and sig in sigs:
                    mismatches.append(f"{sig}: заявлено missing, але є в слоті {slot}")
                    print(f"{sig} slot={slot} pos=? MISMATCH (missing, але знайдено)")
                else:
                    print(f"{sig} slot={slot} pos=- MISSING-OK")
                continue
            if sigs is None:
                mismatches.append(f"{sig}: немає файла блока {slot}")
                print(f"{sig} slot={slot} pos={want_pos} MISMATCH (немає блока)")
                continue
            try:
                have_pos = sigs.index(sig)
            except ValueError:
                mismatches.append(f"{sig}: немає в блоці {slot}")
                print(f"{sig} slot={slot} pos={want_pos} MISMATCH (немає в блоці)")
                continue
            if have_pos != want_pos:
                mismatches.append(f"{sig}: заявлено {want_pos}, у блоці {have_pos}")
                print(f"{sig} slot={slot} pos={want_pos} MISMATCH (блок: {have_pos})")
            else:
                print(f"{sig} slot={slot} pos={want_pos} OK")
    return mismatches


def fetch_block_sigs(rpc_url: str, slot: int) -> list | None:
    """Сигнатури слота з ланцюга через getBlock (jsonParsed або base58-список)."""
    req = {"jsonrpc": "2.0", "id": f"verify-{slot}", "method": "getBlock",
           "params": [slot, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]}
    http_req = urllib.request.Request(
        rpc_url, data=json.dumps(req).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(http_req, timeout=60) as resp:
        result = json.loads(resp.read().decode()).get("result")
    if result is None:
        return None
    sigs = []
    for t in result.get("transactions", []):
        if isinstance(t, dict):
            if "signature" in t:
                sigs.append(t["signature"])
            else:
                inner = t.get("transaction", {})
                arr = inner.get("signatures", [])
                sigs.append(arr[0] if arr else None)
        else:
            sigs.append(t)
    return sigs


def live_check(data_dir: Path, rpc_url: str) -> list:
    """Звірка landed.csv з ланцюгом: позиції перераховуються з живого getBlock."""
    mismatches = []
    with (data_dir / "landed.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            sig, slot = row["signature"], int(row["slot"])
            want_pos = int(row["position"])
            if row.get("status", "landed") == "missing":
                continue  # пропущені слоти жива звірка не покриває
            sigs = fetch_block_sigs(rpc_url, slot)
            if sigs is None:
                print(f"{sig} slot={slot} SKIP (слот пропущено в ланцюгу)")
                continue
            if sig not in sigs:
                mismatches.append(f"{sig}: немає в живому блоці {slot}")
                print(f"{sig} slot={slot} LIVE-MISMATCH (немає в блоці)")
            elif sigs.index(sig) != want_pos:
                mismatches.append(
                    f"{sig}: у landed {want_pos}, у ланцюгу {sigs.index(sig)}")
                print(f"{sig} slot={slot} LIVE-MISMATCH (ланцюг: {sigs.index(sig)})")
            else:
                print(f"{sig} slot={slot} LIVE-OK")
    return mismatches


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        print("використання: python3 scripts/verify.py data/ [--live-check --rpc URL]",
              file=sys.stderr)
        return 2
    if "--live-check" in argv:
        rpc = None
        for i, a in enumerate(argv):
            if a == "--rpc" and i + 1 < len(argv):
                rpc = argv[i + 1]
        rpc = rpc or os.environ.get("RPC_URL")
        if not rpc:
            print("verify: потрібен --rpc URL або RPC_URL", file=sys.stderr)
            return 2
        mismatches = live_check(Path(args[0]), rpc)
        if mismatches:
            print(f"verify: LIVE-MISMATCH — {len(mismatches)}", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            return 1
        print("verify: live-ok — ланцюг підтверджує позиції")
        return 0
    mismatches = verify(Path(args[0]))
    if mismatches:
        print(f"verify: MISMATCH — {len(mismatches)} розбіжностей", file=sys.stderr)
        for m in mismatches:
            print(f"  - {m}", file=sys.stderr)
        return 1
    print("verify: ok — усі позиції збігаються")
    return 0


if __name__ == "__main__":
    sys.exit(main())
