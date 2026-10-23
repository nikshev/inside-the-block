#!/usr/bin/env python3
# impl: FR-001-08
"""Перевірка landed.csv проти сирих блоків data/blocks/*.json.

Контракт: specs/001-pipeline-safety/contracts/verify.md.
Використання: python3 scripts/verify.py data/ [--live-check]
"""

import csv
import json
import sys
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


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--live-check" in argv:
        print("verify: --live-check ще не реалізовано (фіча 002)", file=sys.stderr)
        return 2
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        print("використання: python3 scripts/verify.py data/ [--live-check]", file=sys.stderr)
        return 2
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
