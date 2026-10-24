# impl: FR-002-04, FR-002-05
"""Генератори рукавів A–D з seed-рандомізацією порядку відправки.

Контракт: specs/002-measurement/contracts/arms.md.
"""

from __future__ import annotations

import random

ARMS = ("A", "B", "C", "D")
# Детермінований спільний writable-акаунт рукава D:
# sha256('inside-the-block shared conflict account v1') у base58.
CONFLICT_ACCOUNT = "59qzdJyTmTHLoo4kt1RjEBcuh6EnwbRvNJZAgNE3ATn1"


def _payers(n: int, shared: bool) -> list:
    if shared:
        return ["payer-shared-conflict"] * n
    return [f"payer-pool-{i}" for i in range(n)]


def build_arm_batch(arm: str, seed: int, levels: list, cfg: dict) -> dict:
    """Побудувати опис батча рукава. Повертає dict з txs і send_order."""
    if arm not in ARMS:
        raise ValueError(f"arms: невідомий рукав {arm!r}")
    n = int(cfg.get("tx_per_batch", 8))
    base_limit = int(cfg.get("cu_limit", 200_000))
    txs = []
    if arm == "A":
        prices = list(levels)[:n]
        limits = [base_limit] * n
        payers = _payers(n, False)
        writables = [[] for _ in range(n)]
    elif arm == "B":
        price = int(levels[0]) if levels else 0
        prices = [price] * n
        limits = [base_limit] * n
        payers = _payers(n, False)
        writables = [[] for _ in range(n)]
    elif arm == "C":
        price = int(levels[0]) if levels else 0
        lims = list(levels[1:]) or [base_limit]
        prices = [price] * n
        limits = [lims[i % len(lims)] for i in range(n)]
        payers = _payers(n, False)
        writables = [[] for _ in range(n)]
    else:  # D
        prices = list(levels)[:n]
        limits = [base_limit] * n
        payers = _payers(n, True)
        writables = [[CONFLICT_ACCOUNT] for _ in range(n)]

    for i in range(n):
        txs.append(
            {
                "idx": i,
                "cu_price_lamports": int(prices[i % len(prices)]),
                "cu_limit": int(limits[i % len(limits)]),
                "payer": payers[i],
                "writable_accounts": writables[i],
            }
        )
    order = list(range(n))
    random.Random(seed).shuffle(order)
    return {"arm": arm, "seed": seed, "levels": list(levels), "txs": txs, "send_order": order}
