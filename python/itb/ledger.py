# impl: FR-001-05
"""Append-only леджер витрат. Інваріант: spent_after <= cap (перевіряє pipeline).

Контракт: specs/001-pipeline-safety/contracts/ledger.md.
"""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED = (
    "batch_id",
    "decided_at",
    "config_version",
    "batch_max_lamports",
    "spent_before",
    "spent_after",
    "decision",
    "reason",
)


def append(path, entry: dict) -> None:
    """Дописати один запис. Жодного перезапису історії."""
    missing = [k for k in REQUIRED if k not in entry]
    if missing:
        raise ValueError(f"ledger: бракує полів {missing}")
    if entry["decision"] not in ("accepted", "rejected"):
        raise ValueError("ledger: decision має бути accepted|rejected")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_all(path) -> list:
    """Прочитати всі записи. Порожній файл → []."""
    p = Path(path)
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def spent_total(path) -> int:
    """Сума batch_max лише accepted-записів. Відновлює залишок після перезапуску."""
    total = 0
    for e in load_all(path):
        if e.get("decision") == "accepted":
            total += int(e.get("batch_max_lamports", 0))
    return total
