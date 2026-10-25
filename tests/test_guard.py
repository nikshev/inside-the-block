"""Тест spend guard: чиста функція рішення до будь-якої відправки.

verifies: FR-001-04
"""

from itb.guard import batch_max_for_txs, decide


def test_batch_max_converts_micro_lamports():
    # 10 tx, limit 200000, price 200000 мікро/CU:
    # 5000 + ceil(200000*200000/1e6)=40000 лампортів за tx.
    assert batch_max_for_txs(5000, [(200000, 200000)] * 10) == 450_000
    assert batch_max_for_txs(5000, [(0, 200000)] * 10) == 50_000


def test_accept_when_fits():
    ok, reason = decide(cap=10_000, spent=0, batch_max=11_000 - 1_000)
    assert ok and reason == "ok"


def test_boundary_equal_cap_accepts():
    ok, _ = decide(cap=10_000, spent=4_000, batch_max=6_000)
    assert ok is True


def test_boundary_cap_plus_one_rejects():
    ok, reason = decide(cap=10_000, spent=4_000, batch_max=6_001)
    assert ok is False
    assert reason == "exceeds-cap"


def test_over_cap_rejects():
    ok, reason = decide(cap=10_000, spent=0, batch_max=11_000)
    assert (ok, reason) == (False, "exceeds-cap")


def test_zero_cap_forbids_any_live():
    ok, reason = decide(cap=0, spent=0, batch_max=1)
    assert (ok, reason) == (False, "cap-zero")


def test_empty_batch_rejected():
    ok, reason = decide(cap=10_000, spent=0, batch_max=0)
    assert (ok, reason) == (False, "empty-batch")
