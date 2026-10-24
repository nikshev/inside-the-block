"""Тест аналізу: agreement, tau, пермутації, розриви, вердикти.

Синтетичні фікстури з відомими властивостями, жодної мережі.
verifies: FR-003-01, FR-003-02, FR-003-03, FR-003-04, FR-003-05
"""

import random

from itb import analysis as A


def rows(slot, fees):
    """Батч-фiкстура: позиції 0..n-1, fee за списком (порядок = порядок у блоці)."""
    return [
        {"slot": slot, "batch_id": "b", "signature": f"s{i}", "position": i,
         "status": "landed", "cu_price": f, "send_idx": i}
        for i, f in enumerate(fees)
    ]


class TestAgreement:
    def test_perfect_fee_order(self):
        pairs = A.pairs_in_slot(rows(1, [50, 40, 30, 20, 10]), lambda r: r["cu_price"])
        assert A.agreement(pairs) == 1.0

    def test_random_order_near_half(self):
        rng = random.Random(7)
        fees = list(range(200))
        rng.shuffle(fees)
        pairs = A.pairs_in_slot(rows(1, fees), lambda r: r["cu_price"])
        assert 0.4 < A.agreement(pairs) < 0.6

    def test_ties_excluded(self):
        pairs = A.pairs_in_slot(rows(1, [10, 10, 10]), lambda r: r["cu_price"])
        assert A.agreement(pairs) is None


class TestTau:
    def test_perfect_tau(self):
        b = rows(1, [50, 40, 30, 20, 10])
        assert A.tau_rule(b, lambda r: r["cu_price"]) == 1.0

    def test_pooled_tau_ignores_cross_slot_scale(self):
        # Той самий ідеальний порядок у двох слотах різного розміру:
        # позиції 0..4 і 100..104 — pooled-наївно дасть сміття, послотово 1.0.
        b1 = rows(1, [50, 40, 30, 20, 10])
        b2 = [dict(r, slot=2, position=r["position"] + 100) for r in rows(2, [50, 40, 30, 20, 10])]
        assert A.tau_pooled([b1, b2], lambda r: r["cu_price"]) == 1.0

    def test_pooled_tau_random_near_zero(self):
        import random
        rng = random.Random(11)
        batches = []
        for s in range(5):
            fees = list(range(20))
            rng.shuffle(fees)
            batches.append(rows(s, fees))
        assert abs(A.tau_pooled(batches, lambda r: r["cu_price"])) < 0.2

    def test_bootstrap_ci_perfect_excludes_half(self):
        batches = [rows(s, [50, 40, 30, 20, 10]) for s in range(5)]
        lo, hi = A.bootstrap_ci(batches, lambda r: r["cu_price"], B=200, seed=1)
        assert lo > 0.5 and hi == 1.0


class TestPermutation:
    def test_perfect_p_near_zero(self):
        batches = [rows(s, [50, 40, 30, 20, 10]) for s in range(4)]
        p = A.permutation_p(batches, lambda r: r["cu_price"], P=199, seed=1)
        assert p < 0.05

    def test_random_p_large(self):
        rng = random.Random(3)
        batches = []
        for s in range(10):
            fees = list(range(20))
            rng.shuffle(fees)
            batches.append(rows(s, fees))
        p = A.permutation_p(batches, lambda r: r["cu_price"], P=199, seed=1)
        assert p > 0.05


class TestGaps:
    def test_gap_and_norm_pos(self):
        rs = rows(1, [5, 4, 3])  # позиції 0,1,2 у блоці з 10 tx
        gaps, norm = A.gaps(rs, {1: 10})
        assert gaps == [0, 0]  # сусідні, чужих між нашими немає
        assert norm == [0.0, 0.1, 0.2]

    def test_gap_counts_foreign_between(self):
        rs = [dict(r, position=p) for r, p in zip(rows(1, [5, 4]), [2, 6])]
        gaps, norm = A.gaps(rs, {1: 10})
        assert gaps == [3]
        assert norm == [0.2, 0.6]


class TestVerdict:
    def test_four_classes(self):
        assert A.verdict({"n_pairs": 3, "agreement": 1.0, "ci_low": 1.0,
                          "p_value": 0.0}, 10)[0] == "insufficient-data"
        assert A.verdict({"n_pairs": 100, "agreement": 0.97, "ci_low": 0.9,
                          "p_value": 0.0}, 10)[0] == "strict"
        assert A.verdict({"n_pairs": 100, "agreement": 0.7, "ci_low": 0.55,
                          "p_value": 0.001}, 10)[0] == "statistical"
        assert A.verdict({"n_pairs": 100, "agreement": 0.52, "ci_low": 0.4,
                          "p_value": 0.4}, 10)[0] == "none"
