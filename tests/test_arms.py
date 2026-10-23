"""Тест генераторів рукавів A–D: ізоляція змінних + seed-відтворюваність.

verifies: FR-002-04, FR-002-05
"""

from itb.arms import build_arm_batch


def cfg():
    return {"tx_per_batch": 8, "cu_limit": 200_000}


def test_arm_a_fee_gradient_independent_payers():
    b1 = build_arm_batch("A", seed=7, levels=[0, 100, 500, 1000, 2000, 5000, 10000, 20000], cfg=cfg())
    prices = [t["cu_price_lamports"] for t in b1["txs"]]
    assert len(set(prices)) == 8
    payers = [t["payer"] for t in b1["txs"]]
    assert len(set(payers)) == 8  # пул незалежних
    assert all(t["writable_accounts"] == [] for t in b1["txs"])


def test_arm_b_same_price():
    b = build_arm_batch("B", seed=7, levels=[0], cfg=cfg())
    assert len({t["cu_price_lamports"] for t in b["txs"]}) == 1


def test_arm_c_same_price_different_limits():
    b = build_arm_batch("C", seed=7, levels=[50_000, 100_000, 200_000, 400_000], cfg=cfg())
    assert len({t["cu_limit"] for t in b["txs"]}) > 1
    assert len({t["cu_price_lamports"] for t in b["txs"]}) == 1


def test_arm_d_shared_writable():
    b = build_arm_batch("D", seed=7, levels=[0, 100, 500, 1000, 2000, 5000, 10000, 20000], cfg=cfg())
    shared = {t["writable_accounts"][0] for t in b["txs"]}
    assert len(shared) == 1  # один спільний акаунт
    assert len({t["payer"] for t in b["txs"]}) == 1  # конфлікт fee payer теж спільний


def test_send_order_reproducible_from_seed():
    b1 = build_arm_batch("A", seed=42, levels=list(range(8)), cfg=cfg())
    b2 = build_arm_batch("A", seed=42, levels=list(range(8)), cfg=cfg())
    b3 = build_arm_batch("A", seed=43, levels=list(range(8)), cfg=cfg())
    assert b1["send_order"] == b2["send_order"]
    assert b1["send_order"] != b3["send_order"]
    assert sorted(b1["send_order"]) == list(range(8))
