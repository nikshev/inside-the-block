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
    """Верхня межа комісії батча. УВАГА: priority тут уже в lamports."""
    if num_txs <= 0:
        return 0
    return num_txs * (base_fee_lamports + priority_fee_per_tx)


def batch_max_for_txs(base_fee_lamports: int, prices_limits: list) -> int:
    """Точна верхня межа: сума по tx (base + ceil(price_мікро * limit / 1e6)).

    price — у мікро-лампортах за CU (як у CU price), limit — CU limit.
    Стара помилка: price рахували як лампорти (завищення у ~4000 разів);
    леджер до 2026-10-24 містить консервативні (завищені) записи.
    """
    import math
    total = 0
    for price_micro, limit in prices_limits:
        total += base_fee_lamports + math.ceil(price_micro * limit / 1_000_000)
    return total
