# impl: FR-001-04
"""Spend guard: чиста функція рішення до будь-якої відправки.

Контракт: specs/001-pipeline-safety/contracts/guard.md.
Жодних файлів, мережі, часу — лише (cap, spent, batch_max).
"""

from __future__ import annotations


def decide(cap: int, spent: int, batch_max: int) -> tuple:
    """Повертає (accepted, reason). Межа: spent+max == cap → прийняти."""
    if batch_max <= 0:
        return (False, "empty-batch")
    if cap == 0:
        return (False, "cap-zero")
    if spent + batch_max <= cap:
        return (True, "ok")
    return (False, "exceeds-cap")


def batch_max_lamports(num_txs: int, base_fee_lamports: int, priority_fee_per_tx: int) -> int:
    """Верхня межа комісії батча. Використовується pipeline до виклику decide."""
    if num_txs <= 0:
        return 0
    return num_txs * (base_fee_lamports + priority_fee_per_tx)
