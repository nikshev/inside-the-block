"""Тест analyze CLI на синтетичному data/.

verifies: FR-004-02
"""

import csv
import json
import subprocess
import sys
from pathlib import Path


def make_data(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    (root / "blocks").mkdir(exist_ok=True)
    # Ідеальний рукав A: 3 батчі x 5 tx, fee строго за порядком позицій.
    sent, landed = [], []
    for b in range(3):
        slot = 100 + b
        sigs = []
        for i in range(5):
            fee = 1000 * (5 - i)
            sig = f"sig{b}_{i}"
            sent.append({"batch_id": f"agave-1-A-{b}-7", "idx": i, "signature": sig,
                         "memo_tag": f"x:{i}", "validator_label": "agave-1",
                         "cu_limit": 200000, "cu_price_lamports": fee,
                         "payer": f"p{i}", "sent_at_us": i, "path": "stub-local",
                         "target_slot": slot, "config_version": "v1",
                         "stub_signature": False, "send_idx": i})
            landed.append({"signature": sig, "slot": slot, "position": i,
                           "batch_id": f"agave-1-A-{b}-7", "idx": i, "status": "landed"})
            sigs.append(sig)
        (root / "blocks" / f"{slot}.json").write_text(
            json.dumps({"slot": slot, "encoding": "stub",
                        "block": {"transactions": [{"signature": s} for s in sigs]}}),
            encoding="utf-8")
    with (root / "sent.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sent[0].keys()))
        w.writeheader()
        w.writerows(sent)
    with (root / "landed.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(landed[0].keys()))
        w.writeheader()
        w.writerows(landed)


def test_analyze_strict_on_perfect_arm(tmp_path):
    make_data(tmp_path / "data")
    p = subprocess.run([sys.executable, "scripts/analyze.py", str(tmp_path / "data"),
                        "--min-pairs", "5"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert "strict" in p.stdout
    assert "agave-1" in p.stdout


def test_analyze_by_leader(tmp_path):
    make_data(tmp_path / "data2")
    (tmp_path / "data2" / "leaders.json").write_text(
        json.dumps({"target": "x", "slots": {"100": "LEADaaa111", "101": "LEADaaa111",
                                             "102": "LEADaaa111"}}))
    p = subprocess.run([sys.executable, "scripts/analyze.py", str(tmp_path / "data2"),
                        "--min-pairs", "5", "--by-leader"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert "LEADaaa1" in p.stdout
