#!/usr/bin/env python3
# impl: FR-004-01, FR-004-04, FR-004-05
"""Check submission docs completeness (дублюється в tests/test_docs.py).

Run: python3 scripts/check_docs.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECKS = {
    "README.md": (
        ["docker compose up", "MODE=live",
         "Leader schedule", "Backend path", "Our tx interaction",
         "Block competition", "Send order", "Noise vs rule"],
        ["час надходження", "паралельне виконання", "налаштування оператора"],
    ),
    "docs/report.md": (
        [],
        ["dates", "version", "verdict", "chart", "what went wrong"],
    ),
    "docs/submission.md": (
        [],
        ["code", "single command", "keys", "dry-run", "raw data",
         "verify", "readme", "report"],
    ),
}


def check() -> list:
    """Returns list of violations (empty = docs complete)."""
    problems = []
    for name, (required, required_low) in CHECKS.items():
        p = ROOT / name
        if not p.is_file():
            problems.append(f"{name} missing")
            continue
        text = p.read_text(encoding="utf-8")
        for needle in required:
            if needle not in text:
                problems.append(f"{name}: missing {needle!r}")
        low = text.lower()
        for needle in required_low:
            if needle not in low:
                problems.append(f"{name}: missing {needle!r} (case-insensitive)")
    return problems


def main() -> int:
    problems = check()
    if problems:
        print("check_docs: INCOMPLETE DOCUMENTS", file=sys.stderr)
        for pr in problems:
            print(f"  - {pr}", file=sys.stderr)
        return 1
    print("check_docs: ok — README, report, submission повні")
    return 0


if __name__ == "__main__":
    sys.exit(main())
