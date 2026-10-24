#!/usr/bin/env python3
# impl: FR-004-02
"""Метрики упорядкування з data/: python3 scripts/analyze.py data/ [--min-pairs N].

Групує за (validator_label, arm) — arm витягується з batch_id
формату <label>-<A|B|C|D>-<seq>-<seed>.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from itb import analysis as A
from itb import report as R


def parse_arm(batch_id: str) -> str:
    """Одинарна літера A–D у batch_id."""
    for part in batch_id.split("-"):
        if len(part) == 1 and part in "ABCD":
            return part
    return "?"


def load_joined(data_dir: Path) -> list:
    """Landed ⨝ sent за сигнатурою (ключі: fee, reward/cost, send_idx)."""
    sent = {}
    with (data_dir / "sent.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            sent[row["signature"]] = row
    out = []
    with (data_dir / "landed.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status", "landed") != "landed":
                continue
            s = sent.get(row["signature"], {})
            try:
                price = int(s.get("cu_price_lamports", 0))
                limit = int(s.get("cu_limit", 200_000)) or 200_000
            except ValueError:
                price, limit = 0, 200_000
            out.append({
                "slot": int(row["slot"]),
                "batch_id": row.get("batch_id", ""),
                "validator": s.get("validator_label", "?"),
                "arm": parse_arm(row.get("batch_id", "")),
                "signature": row["signature"],
                "position": int(row["position"]),
                "cu_price": price,
                "reward_per_cu": price / limit,
                "send_idx": int(s.get("send_idx", s.get("idx", 0))),
            })
    return out


def analyze(data_dir: Path, min_pairs: int = 30) -> list:
    """Метрики на (validator, arm)."""
    rows = load_joined(data_dir)
    groups: dict = {}
    for r in rows:
        groups.setdefault((r["validator"], r["arm"]), []).append(r)
    results = []
    for (validator, arm), rs in sorted(groups.items()):
        batches: dict = {}
        for r in rs:
            batches.setdefault((r["slot"], r["batch_id"]), []).append(r)
        blist = list(batches.values())
        agr = {
            "fee": A.agreement(A.pairs_in_slot(rs, lambda r: r["cu_price"])),
            "reward": A.agreement(A.pairs_in_slot(rs, lambda r: r["reward_per_cu"])),
            "send": A.agreement(A.pairs_in_slot(rs, lambda r: r["send_idx"])),
        }
        n_pairs = sum(1 for p in A.pairs_in_slot(rs, lambda r: r["cu_price"]) if not p["tie"])
        tau = A.tau_pooled(blist, lambda r: r["cu_price"])
        lo, hi = A.bootstrap_ci(blist, lambda r: r["cu_price"], B=200, seed=7)
        p = A.permutation_p(blist, lambda r: r["cu_price"], P=199, seed=11)
        label, reason = A.verdict(
            {"n_pairs": n_pairs, "agreement": agr["fee"] if agr["fee"] is not None else 0.0,
             "ci_low": lo, "p_value": p}, min_pairs)
        results.append({"validator": validator, "arm": arm, "n_pairs": n_pairs,
                        "agreement": agr, "tau": tau, "ci_low": lo, "ci_high": hi,
                        "p_value": p, "verdict": label, "reason": reason})
    return results


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("використання: python3 scripts/analyze.py data/ [--min-pairs N]",
              file=sys.stderr)
        return 2
    min_pairs = 30
    for i, a in enumerate(argv):
        if a == "--min-pairs" and i + 1 < len(argv):
            min_pairs = int(argv[i + 1])
    results = analyze(Path(args[0]), min_pairs)
    print(R.render_markdown(results, source=args[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
