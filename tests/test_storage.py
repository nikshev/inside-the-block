"""Тест розкладки сирих даних: фиксированные заголовки, missing-статус.

verifies: FR-001-07
"""

import csv
import json

from itb.storage import save_block, save_snapshot, write_landed, write_sent


def test_sent_landed_roundtrip(tmp_path):
    data = tmp_path / "data"
    txs = [
        {
            "batch_id": "b1",
            "idx": 0,
            "signature": "sigA",
            "memo_tag": "b1:0",
            "validator_label": "agave-1",
            "cu_limit": 200_000,
            "cu_price_lamports": 0,
            "payer": "payer-pool-0",
            "sent_at_us": 1,
            "path": "stub-local",
            "target_slot": 100,
            "config_version": "v1",
            "stub_signature": True,
        }
    ]
    write_sent(data, txs)
    with (data / "sent.csv").open(encoding="utf-8") as f:
        assert f.readline().strip().startswith("batch_id,idx,signature,")
        rows = list(csv.DictReader([f.readline().strip()] and open(data / "sent.csv", encoding="utf-8")))
        assert rows[0]["signature"] == "sigA"

    write_landed(data, [{"signature": "sigA", "slot": 100, "position": 3,
                         "batch_id": "b1", "idx": 0, "status": "landed"}])
    write_landed(data, [{"signature": "sigB", "slot": 101, "position": -1,
                         "batch_id": "b1", "idx": 1, "status": "missing"}])
    landed = (data / "landed.csv").read_text(encoding="utf-8")
    assert "missing" in landed

    save_block(data, 100, {"transactions": [{"signature": "sigA"}]}, encoding="stub")
    assert json.loads((data / "blocks" / "100.json").read_text(encoding="utf-8"))["encoding"] == "stub"

    save_snapshot(data, {"measured_at": "t", "validators": []})
    assert (data / "validators_snapshot.json").is_file()
