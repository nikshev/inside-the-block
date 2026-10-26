#!/usr/bin/env python3
# impl: FR-004-01, FR-004-04, FR-004-05
"""Check submission documentation completeness.

Run: python3 scripts/check_docs.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGLISH_DOCS = (
    "README.md",
    "docs/report.md",
    "docs/submission.md",
    "docs/validators.md",
    "docs/local-dev.md",
    "docs/traceability.md",
)

CHECKS = {
    "README.md": (
        ["docker compose up", "MODE=live",
         "Leader schedule", "Backend-to-node delivery path",
         "Interactions among our transactions", "Competition from other block transactions",
         "Send order", "Noise versus signal"],
        ["arrival time", "parallel banking-thread execution", "operator config"],
    ),
    "docs/report.md": (
        [],
        ["measurement dates", "config", "verdict", "chart", "what went wrong"],
    ),
    "docs/submission.md": (
        [],
        ["code", "one-command", "keys", "dry-run", "raw mainnet records",
         "verify", "readme", "report"],
    ),
}


def check() -> list:
    """Returns list of violations (empty = docs complete)."""
    problems = []
    for name in ENGLISH_DOCS:
        p = ROOT / name
        if not p.is_file():
            problems.append(f"{name} missing")
            continue
        text = p.read_text(encoding="utf-8")
        if any("\u0400" <= ch <= "\u04ff" for ch in text):
            problems.append(f"{name}: contains untranslated Cyrillic text")
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
    print("check_docs: ok — README, report, and submission docs are complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
