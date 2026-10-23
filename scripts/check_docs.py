#!/usr/bin/env python3
# impl: FR-004-01, FR-004-04, FR-004-05
"""Перевірка повноти документів сабміту (дублюється в tests/test_docs.py).

Запуск: python3 scripts/check_docs.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECKS = {
    "README.md": (
        ["docker compose up", "MODE=live",
         "Leader schedule", "Шлях від бекенду", "Взаємодія наших tx",
         "Конкуренція в блоці", "Порядок відправки", "Шум проти правила"],
        ["час надходження", "паралельне виконання", "налаштування оператора"],
    ),
    "docs/report.md": (
        [],
        ["дати", "версі", "вердикт", "графік", "що пішло не так"],
    ),
    "docs/submission.md": (
        [],
        ["код", "однією командою", "ключі", "dry-run", "сирі дані",
         "verify", "readme", "звіт"],
    ),
}


def check() -> list:
    """Повертає список порушень (порожній = документи повні)."""
    problems = []
    for name, (required, required_low) in CHECKS.items():
        p = ROOT / name
        if not p.is_file():
            problems.append(f"{name} відсутній")
            continue
        text = p.read_text(encoding="utf-8")
        for needle in required:
            if needle not in text:
                problems.append(f"{name}: немає {needle!r}")
        low = text.lower()
        for needle in required_low:
            if needle not in low:
                problems.append(f"{name}: немає {needle!r} (case-insensitive)")
    return problems


def main() -> int:
    problems = check()
    if problems:
        print("check_docs: НЕПОВНІ ДОКУМЕНТИ", file=sys.stderr)
        for pr in problems:
            print(f"  - {pr}", file=sys.stderr)
        return 1
    print("check_docs: ok — README, report, submission повні")
    return 0


if __name__ == "__main__":
    sys.exit(main())
