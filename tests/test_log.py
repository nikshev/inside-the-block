"""Тест JSON-логера: обов'язкові поля, мікросекунди, жодних секретів.

verifies: FR-001-06
"""

import json

import pytest

from itb.log import emit


def test_emit_adds_ts_and_keeps_fields(capsys):
    emit({"batch_id": "b1", "mode": "dry-run", "config_version": "v1", "msg": "hello"})
    line = capsys.readouterr().out.strip()
    rec = json.loads(line)
    assert rec["batch_id"] == "b1"
    assert isinstance(rec["ts_us"], int)


def test_missing_required_field_fails():
    with pytest.raises(ValueError):
        emit({"batch_id": "b1", "mode": "dry-run", "msg": "без версії"})


def test_no_secrets_in_output(capsys):
    emit(
        {
            "batch_id": "b1",
            "mode": "dry-run",
            "config_version": "v1",
            "msg": "batch ready",
            "path": "stub-local",
        }
    )
    out = capsys.readouterr().out.lower()
    assert "private" not in out and "secret" not in out and "mnemonic" not in out
