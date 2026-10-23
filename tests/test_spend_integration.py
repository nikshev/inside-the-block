"""Інтеграція guard→ledger→pipeline: два батчі, другий перевищує cap.

verifies: FR-001-04, FR-001-05
"""

from itb.config import load
from itb.ledger import spent_total
from itb.pipeline import run


def make_cfg(cap):
    return load(
        {
            "config_version": "2026.10.23.1",
            "spend_cap_lamports": cap,
            "base_fee_lamports": 5000,
            "batch": {"tx_per_batch": 8, "cu_limit": 200_000, "cu_price_lamports": 0},
            "validators": [
                {"identity": "V1", "label": "agave-1", "expected_client": "agave"},
                {"identity": "V2", "label": "agave-2", "expected_client": "agave"},
            ],
            "rpc": {"http_url_ref": "env:RPC_URL", "ws_url_ref": "env:WS_URL"},
        }
    )


def test_second_batch_rejected_and_total_within_cap(tmp_path):
    # batch_max = 8 * 5000 = 40_000; cap 50_000: перший accepted, другий rejected
    cfg = make_cfg(50_000)
    calls = []
    report = run(
        cfg, mode="live", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl",
        sender=lambda txs: calls.append(txs),
        emit=lambda r: None,
    )
    assert report == {"mode": "live", "accepted": 1, "rejected": 1}
    assert len(calls) == 1
    assert spent_total(tmp_path / "ledger.jsonl") == 40_000
