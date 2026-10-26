"""Тест графіків: SVG-скатер з точками всіх tx і підписаними осями.

verifies: FR-004-04
"""

import csv
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def make_data(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    sent = [{"batch_id": f"b&{i}", "idx": i, "signature": f"s{i}",
             "memo_tag": f"b1:{i}", "validator_label": "L",
             "cu_limit": 200000, "cu_price_lamports": 1000 * (i + 1),
             "payer": "p", "sent_at_us": i, "path": "rpc",
             "target_slot": 7, "config_version": "v1", "stub_signature": False,
             "send_pos": i} for i in range(5)]
    with (root / "sent.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sent[0].keys()))
        w.writeheader()
        w.writerows(sent)
    landed = [{"signature": f"s{i}", "slot": 7 + i, "position": 4 - i,
               "batch_id": f"b&{i}", "idx": i, "status": "landed"}
              for i in range(5)]
    with (root / "landed.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(landed[0].keys()))
        w.writeheader()
        w.writerows(landed)
    (root / "leaders.json").write_text(json.dumps({"slots": {"7": "LeaderOne"}}))
    return landed


def test_plot_writes_svg_with_points(tmp_path):
    landed = make_data(tmp_path / "data")
    out = tmp_path / "plot.svg"
    p = subprocess.run([sys.executable, "scripts/plot.py", str(tmp_path / "data"),
                        "--out", str(out)], capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    text = out.read_text(encoding="utf-8")
    assert text.count("<circle") == 5
    assert "CU price" in text and "position" in text

    svg = ET.fromstring(text)
    namespace = "{http://www.w3.org/2000/svg}"
    circles = svg.findall(f".//{namespace}circle")
    for row, circle in zip(landed, circles):
        point_title = circle.find(f"{namespace}title").text
        assert f"slot={row['slot']} batch_id={row['batch_id']}" in point_title
