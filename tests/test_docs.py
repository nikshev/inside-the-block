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
    for point in ["Leader schedule", "Backend-to-node delivery path",
                  "Interactions among our transactions",
                  "Competition from other block transactions", "Send order",
                  "Noise versus signal"]:
        assert point in t, f"missing design validity point: {point}"
    for nonsep in ["arrival time", "parallel banking-thread execution", "operator config"]:
        assert nonsep in t.lower(), f"missing non-separated: {nonsep}"
    assert "spend" in t.lower() and "keys" in t.lower()


def test_report_skeleton():
    t = read("docs/report.md")
    for section in ["dates", "versions", "verdict", "chart", "what went wrong"]:
        assert section in t.lower(), f"missing report section: {section}"


def test_submission_checklist():
    t = read("docs/submission.md")
    for item in ["code", "one-command", "keys", "dry-run", "raw mainnet records",
                 "verify", "readme", "report"]:
        assert item in t.lower(), f"missing deliverable: {item}"


def test_submission_documents_are_in_english():
    for name in ["README.md", "docs/report.md", "docs/submission.md",
                 "docs/validators.md", "docs/local-dev.md", "docs/traceability.md"]:
        text = read(name)
        assert not any("\u0400" <= ch <= "\u04ff" for ch in text), \
            f"untranslated Cyrillic text in {name}"
