"""Тест append-only леджера витрат з відновленням після перезапуску.

verifies: FR-001-05
"""

from itb.ledger import append, spent_total


def entry(batch_id, max_fee, spent_before, decision, reason="ok"):
    return {
        "batch_id": batch_id,
        "decided_at": "2026-10-23T00:00:00Z",
        "config_version": "2026.10.23.1",
        "batch_max_lamports": max_fee,
        "spent_before": spent_before,
        "spent_after": spent_before + (max_fee if decision == "accepted" else 0),
        "decision": decision,
        "reason": reason,
    }


def test_append_and_total(tmp_path):
    p = tmp_path / "ledger.jsonl"
    append(p, entry("b1", 6_000, 0, "accepted"))
    append(p, entry("b2", 5_000, 6_000, "rejected", "exceeds-cap"))
    assert spent_total(p) == 6_000
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_recovery_after_reopen(tmp_path):
    p = tmp_path / "ledger.jsonl"
    append(p, entry("b1", 6_000, 0, "accepted"))
    first = spent_total(p)  # ніби перезапуск: читаємо з диска заново
    append(p, entry("b2", 3_000, first, "accepted"))
    assert spent_total(p) == 9_000


def test_rejected_does_not_raise_spent(tmp_path):
    p = tmp_path / "ledger.jsonl"
    append(p, entry("b1", 11_000, 0, "rejected", "exceeds-cap"))
    assert spent_total(p) == 0
