"""Тест вікон лідера і snapshot версій на записаних фікстурах RPC.

verifies: FR-002-06
"""

from itb.schedule import snapshot, windows

SCHEDULE = {
    "V1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": [10, 11, 12, 30],
    "V2BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB": [13, 14],
}

NODES = [
    {"pubkey": "V1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "version": "3.0.1"},
    {"pubkey": "V2BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB", "version": "2.1.0-jito"},
]


def test_windows_groups_consecutive_slots():
    w = windows(SCHEDULE, "V1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", epoch=5)
    assert [(x["start_slot"], x["end_slot"]) for x in w] == [(10, 12), (30, 30)]
    assert all(x["epoch"] == 5 for x in w)


def test_windows_unknown_validator_empty():
    assert windows(SCHEDULE, "NOBODY", epoch=5) == []


def test_snapshot_records_versions():
    s = snapshot(NODES, source="test")
    by_id = {v["identity"]: v["version"] for v in s["validators"]}
    assert by_id["V1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"] == "3.0.1"
    assert s["source"] == "test"
