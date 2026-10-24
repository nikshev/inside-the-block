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


def load_joined(data_dir: Path, by_leader: bool = False) -> list:
    """Landed ⨝ sent за сигнатурою (ключі: fee, reward/cost, send_idx).

    by_leader: мітка групи — фактичний лідер слота (leaders.json),
    інакше — validator_label з sent.csv.
    """
    leaders = {}
    if by_leader:
        lp = data_dir / "leaders.json"
        if lp.is_file():
            leaders = json.loads(lp.read_text(encoding="utf-8")).get("slots", {})
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
            label = s.get("validator_label", "?")
            if by_leader:
                label = leaders.get(str(row["slot"]), label)[:8]
            out.append({
                "slot": int(row["slot"]),
                "batch_id": row.get("batch_id", ""),
                "validator": label,
                "arm": parse_arm(row.get("batch_id", "")),
                "signature": row["signature"],
                "position": int(row["position"]),
                "cu_price": price,
                "reward_per_cu": price / limit,
                # send_pos = реальне місце в порядку відправки; fallback idx
                # лише для старих CSV без колонки (H1 за ними недійсний).
                "send_idx": int(s.get("send_pos", s.get("send_idx", s.get("idx", 0)))),
            })
    return out


def analyze(data_dir: Path, min_pairs: int = 30, by_leader: bool = False) -> list:
    """Метрики на (validator, arm)."""
    rows = load_joined(data_dir, by_leader=by_leader)
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
    by_leader = "--by-leader" in argv
    for i, a in enumerate(argv):
        if a == "--min-pairs" and i + 1 < len(argv):
            min_pairs = int(argv[i + 1])
    results = analyze(Path(args[0]), min_pairs, by_leader=by_leader)
    print(R.render_markdown(results, source=args[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
