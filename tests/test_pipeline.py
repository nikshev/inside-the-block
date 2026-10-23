"""Тест оркестратора: dry-run зупиняється до sender, live йде через guard.

verifies: FR-001-01, FR-001-02
"""

from pathlib import Path

import pytest

from itb.config import load


def make_cfg(**over):
    d = {
        "config_version": "2026.10.23.1",
        "spend_cap_lamports": 50_000_000,
        "base_fee_lamports": 5000,
        "batch": {"tx_per_batch": 8, "cu_limit": 200_000, "cu_price_lamports": 0},
        "validators": [
            {"identity": "V1", "label": "agave-1", "expected_client": "agave"},
            {"identity": "V2", "label": "jito-1", "expected_client": "jito-solana"},
        ],
        "rpc": {"http_url_ref": "env:RPC_URL", "ws_url_ref": "env:WS_URL"},
    }
    d.update(over)
    return load(d)


def test_dryrun_never_calls_sender_and_no_ledger(tmp_path):
    from itb.pipeline import run

    cfg = make_cfg()
    calls = []
    logs = []
    report = run(
        cfg, mode="dry-run", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl",
        sender=lambda txs: calls.append(txs),
        emit=lambda r: logs.append(r),
    )
    assert calls == []
    assert not (tmp_path / "ledger.jsonl").is_file()
    assert report["mode"] == "dry-run"
    assert any(l.get("msg") == "would-stop-before-send" for l in logs)
    assert all(l.get("config_version") == "2026.10.23.1" for l in logs)


def test_live_calls_sender_when_cap_allows(tmp_path):
    from itb.pipeline import run

    cfg = make_cfg()
    calls = []
    report = run(
        cfg, mode="live", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl",
        sender=lambda txs: calls.append(txs),
        emit=lambda r: None,
    )
    assert len(calls) == 2  # по одному батчу на валідатора
    assert (tmp_path / "ledger.jsonl").is_file()
    assert report["accepted"] == 2


def test_live_blocked_when_cap_zero(tmp_path):
    from itb.pipeline import run

    cfg = make_cfg(spend_cap_lamports=0)
    calls = []
    report = run(
        cfg, mode="live", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl",
        sender=lambda txs: calls.append(txs),
        emit=lambda r: None,
    )
    assert calls == []
    assert report["accepted"] == 0
    assert report["rejected"] == 2


def test_unknown_mode_fails():
    from itb.pipeline import run

    with pytest.raises(ValueError):
        run(make_cfg(), mode="send-everything", data_dir=Path("/tmp/x"),
            ledger_path=Path("/tmp/x/ledger.jsonl"))
