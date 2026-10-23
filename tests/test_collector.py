"""Тест збирача позицій: 3 слоти, 15 tx, один слот пропущено.

verifies: FR-002-09
"""

import csv

from itb.collector import collect


def make_sent(data, rows):
    with (data / "sent.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["batch_id", "idx", "signature", "target_slot"])
        w.writeheader()
        w.writerows(rows)


def test_collect_positions_and_missing(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    rows = [{"batch_id": "b1", "idx": i, "signature": f"sig{i}", "target_slot": 100 + (i // 6)}
            for i in range(15)]
    make_sent(data, rows)
    blocks = {
        100: {"transactions": [{"signature": f"sig{i}"} for i in range(6)]},
        101: None,  # пропущений слот
        102: {"transactions": [{"signature": "junk"}, {"signature": "sig12"},
                               {"signature": "sig13"}, {"signature": "sig14"}]},
    }
    # sig6..sig11 цілили в 101, але потрапили... ні: їх нема в блоці 102 крім 12-14.
    # Правило: шукаємо сигнатуру в блоці цільового слота.
    report = collect(data, lambda slot: blocks.get(slot))
    by_sig = {r["signature"]: r for r in report}
    assert by_sig["sig0"]["position"] == 0
    assert by_sig["sig12"]["position"] == 1  # після junk
    assert by_sig["sig6"]["status"] == "missing"
    assert by_sig["sig14"]["status"] == "landed"
    assert (data / "landed.csv").is_file()
    assert (data / "blocks" / "100.json").is_file()
