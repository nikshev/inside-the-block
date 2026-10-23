"""Тест повноти документів сабміту (тонка обгортка над scripts/check_docs.py).

verifies: FR-004-01, FR-004-04, FR-004-05
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(name):
    p = ROOT / name
    assert p.is_file(), f"{name} відсутній"
    return p.read_text(encoding="utf-8")


def test_check_docs_script_green():
    p = subprocess.run([sys.executable, "scripts/check_docs.py"],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr


def test_readme_design_validity():
    t = read("README.md")
    assert "docker compose up" in t
    assert "MODE=live" in t
    for point in ["Leader schedule", "Шлях від бекенду", "Взаємодія наших tx",
                  "Конкуренція в блоці", "Порядок відправки", "Шум проти правила"]:
        assert point in t, f"немає пункту design validity: {point}"
    for nonsep in ["час надходження", "паралельне виконання", "налаштування оператора"]:
        assert nonsep in t.lower(), f"немає невідокремленого: {nonsep}"
    assert "spend" in t.lower() and "keys" in t.lower()


def test_report_skeleton():
    t = read("docs/report.md")
    for section in ["дати", "версі", "вердикт", "графік", "що пішло не так"]:
        assert section in t.lower(), f"немає розділу звіту: {section}"


def test_submission_checklist():
    t = read("docs/submission.md")
    for item in ["код", "однією командою", "ключі", "dry-run", "сирі дані",
                 "verify", "readme", "звіт"]:
        assert item in t.lower(), f"немає deliverable: {item}"
