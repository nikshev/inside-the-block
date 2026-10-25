"""Тест графіків: SVG-скатер з точками всіх tx і підписаними осями.

verifies: FR-004-04
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def make_data(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    sent = [{"batch_id": "b1", "idx": i, "signature": f"s{i}",
             "memo_tag": f"b1:{i}", "validator_label": "L",
             "cu_limit": 200000, "cu_price_lamports": 1000 * (i + 1),
             "payer": "p", "sent_at_us": i, "path": "rpc",
             "target_slot": 7, "config_version": "v1", "stub_signature": False,
             "send_pos": i} for i in range(5)]
    with (root / "sent.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sent[0].keys()))
        w.writeheader()
        w.writerows(sent)
    landed = [{"signature": f"s{i}", "slot": 7, "position": 4 - i,
               "batch_id": "b1", "idx": i, "status": "landed"} for i in range(5)]
    with (root / "landed.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(landed[0].keys()))
        w.writeheader()
        w.writerows(landed)
    (root / "leaders.json").write_text(json.dumps({"slots": {"7": "LeaderOne"}}))


def test_plot_writes_svg_with_points(tmp_path):
    make_data(tmp_path / "data")
    out = tmp_path / "plot.svg"
    p = subprocess.run([sys.executable, "scripts/plot.py", str(tmp_path / "data"),
                        "--out", str(out)], capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    text = out.read_text(encoding="utf-8")
    assert text.count("<circle") == 5
    assert "CU price" in text and "position" in text
