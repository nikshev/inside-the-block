"""Тест verify: 100% збіг на фікстурі, MISMATCH ловиться з сигнатурою.

verifies: FR-001-08
"""

import csv
import json
import subprocess
import sys


def write_data(root, landed_rows, blocks):
    (root / "blocks").mkdir(parents=True, exist_ok=True)
    with (root / "landed.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["signature", "slot", "position", "batch_id", "idx", "status"])
        w.writeheader()
        w.writerows(landed_rows)
    for slot, sigs in blocks.items():
        (root / "blocks" / f"{slot}.json").write_text(
            json.dumps({"slot": slot, "encoding": "stub",
                        "block": {"transactions": [{"signature": s} for s in sigs]}}),
            encoding="utf-8",
        )


def run_verify(root, *args):
    return subprocess.run(
        [sys.executable, "scripts/verify.py", str(root), *args],
        capture_output=True, text=True,
    )


def test_verify_all_match(tmp_path):
    sigs = [f"sig{i}" for i in range(10)]
    write_data(
        tmp_path,
        [{"signature": s, "slot": 100, "position": i,
          "batch_id": "b1", "idx": i, "status": "landed"} for i, s in enumerate(sigs)],
        {100: sigs},
    )
    p = run_verify(tmp_path)
    assert p.returncode == 0, p.stderr


def test_verify_catches_mismatch_with_signature(tmp_path):
    sigs = [f"sig{i}" for i in range(10)]
    rows = [{"signature": s, "slot": 100, "position": i,
             "batch_id": "b1", "idx": i, "status": "landed"} for i, s in enumerate(sigs)]
    rows[4]["position"] = 7  # навмисне зіпсовано
    write_data(tmp_path, rows, {100: sigs})
    p = run_verify(tmp_path)
    assert p.returncode == 1
    assert "sig4" in (p.stdout + p.stderr)


def test_verify_missing_slot_ok(tmp_path):
    write_data(
        tmp_path,
        [{"signature": "sigX", "slot": 999, "position": -1,
          "batch_id": "b1", "idx": 0, "status": "missing"}],
        {},
    )
    assert run_verify(tmp_path).returncode == 0
