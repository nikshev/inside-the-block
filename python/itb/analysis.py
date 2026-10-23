# impl: FR-003-01, FR-003-02, FR-003-03, FR-003-04, FR-003-05
"""Статистика упорядкування: пари, agreement, Kendall τ, пермутації, вердикти.

Тільки stdlib. Усі пари — всередині одного слота; bootstrap — по батчах.
"""

from __future__ import annotations

import random
import statistics


def pairs_in_slot(landed_rows: list, key_of) -> list:
    """Усі невпорядковані пари tx одного слота. tie=True при рівних ключах."""
    by_slot: dict = {}
    for r in landed_rows:
        if r.get("status", "landed") != "landed":
            continue
        by_slot.setdefault(r["slot"], []).append(r)
    pairs = []
    for rows in by_slot.values():
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                ka, kb = key_of(a), key_of(b)
                pairs.append({"pos_a": a["position"], "pos_b": b["position"],
                              "key_a": ka, "key_b": kb, "tie": ka == kb})
    return pairs


def agreement(pairs: list) -> float | None:
    """Частка нетієвих пар, де раніша позиція має вищий ключ. Безлад = 0.5."""
    decided = [p for p in pairs if not p["tie"]]
    if not decided:
        return None
    good = sum(1 for p in decided
               if (p["pos_a"] < p["pos_b"]) == (p["key_a"] > p["key_b"]))
    return good / len(decided)


def _tau_a(xs: list, ys: list) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (xs[i] - xs[j]) * (ys[i] - ys[j])
            if s > 0:
                conc += 1
            elif s < 0:
                disc += 1
    tot = n * (n - 1) / 2
    return (conc - disc) / tot


def tau_rule(batch_rows: list, key_of) -> float:
    """+1 = ідеальне слідування правилу (вищий ключ → раніша позиція)."""
    xs = [key_of(r) for r in batch_rows]
    ys = [r["position"] for r in batch_rows]
    return -_tau_a(xs, ys)


def _pooled_agreement(batches: list, key_of) -> float | None:
    pairs = []
    for b in batches:
        pairs.extend(pairs_in_slot(b, key_of))
    return agreement(pairs)


def bootstrap_ci(batches: list, key_of, B: int = 1000, seed: int = 0) -> tuple:
    """95% CI статистики agreement ресемплінгом батчів."""
    rng = random.Random(seed)
    stats = []
    for _ in range(B):
        sample = [rng.choice(batches) for _ in batches]
        v = _pooled_agreement(sample, key_of)
        if v is not None:
            stats.append(v)
    if not stats:
        return (0.0, 0.0)
    stats.sort()
    lo = stats[max(0, int(0.025 * len(stats)))]
    hi = stats[min(len(stats) - 1, int(0.975 * len(stats)))]
    return (lo, hi)


def permutation_p(batches: list, key_of, P: int = 999, seed: int = 0) -> float:
    """p-value проти H0: перестановки позицій усередині батчів."""
    obs = _pooled_agreement(batches, key_of)
    if obs is None:
        return 1.0
    rng = random.Random(seed)
    ge = 0
    for _ in range(P):
        perm = []
        for b in batches:
            pos = [r["position"] for r in b]
            rng.shuffle(pos)
            perm.append([dict(r, position=p) for r, p in zip(b, pos)])
        v = _pooled_agreement(perm, key_of)
        if v is not None and v >= obs:
            ge += 1
    return (1 + ge) / (1 + P)


def gaps(landed_rows: list, block_sizes: dict) -> tuple:
    """Чужі tx між сусідніми нашими + нормовані позиції (0–1)."""
    by_slot: dict = {}
    for r in landed_rows:
        if r.get("status", "landed") != "landed":
            continue
        by_slot.setdefault(r["slot"], []).append(r["position"])
    gap_list, norm_list = [], []
    for slot, poss in by_slot.items():
        poss = sorted(poss)
        size = block_sizes.get(slot, max(poss) + 1 if poss else 1)
        norm_list.extend([p / size for p in poss])
        gap_list.extend([b - a - 1 for a, b in zip(poss, poss[1:])])
    return (gap_list, norm_list)


def verdict(m: dict, min_pairs: int) -> tuple:
    """Правило рішення PRD: 4 класи."""
    if m.get("n_pairs", 0) < min_pairs:
        return ("insufficient-data", f"пар {m.get('n_pairs', 0)} < {min_pairs}")
    agr = m.get("agreement")
    if agr is not None and agr >= 0.95 and (m.get("ci_low") or 0) > 0.5:
        return ("strict", f"agreement {agr:.3f}, CI нижче {m['ci_low']:.3f} > 0.5")
    if (m.get("p_value") if m.get("p_value") is not None else 1) < 0.01:
        return ("statistical", f"p={m['p_value']:.4f} < 0.01, але є винятки")
    return ("none", f"жодна гіпотеза не відрізняється від H0 (p={m.get('p_value')})")


def median(xs: list) -> float | None:
    """Медіана або None на порожньому."""
    if not xs:
        return None
    return statistics.median(xs)
