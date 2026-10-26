"""Test submission docs completeness (thin wrapper over scripts/check_docs.py).

verifies: FR-004-01, FR-004-04, FR-004-05
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(name):
    p = ROOT / name
    assert p.is_file(), f"{name} missing"
    return p.read_text(encoding="utf-8")


def test_check_docs_script_green():
    p = subprocess.run([sys.executable, "scripts/check_docs.py"],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr


def test_readme_design_validity():
    t = read("README.md")
    assert "docker compose up" in t
    assert "MODE=live" in t
    for point in ["Leader schedule", "Path from backend", "Our tx interaction",
                  "Competition in block", "Send order", "Noise vs rule"]:
        assert point in t, f"missing design validity point: {point}"
    for nonsep in ["arrival time", "parallel execution", "operator config"]:
        assert nonsep in t.lower(), f"missing non-separated: {nonsep}"
    assert "spend" in t.lower() and "keys" in t.lower()


def test_report_skeleton():
    t = read("docs/report.md")
    for section in ["dates", "versions", "verdict", "chart", "what went wrong"]:
        assert section in t.lower(), f"missing report section: {section}"


def test_submission_checklist():
    t = read("docs/submission.md")
    for item in ["code", "single command", "keys", "dry-run", "raw data",
                 "verify", "readme", "report"]:
        assert item in t.lower(), f"missing deliverable: {item}"
