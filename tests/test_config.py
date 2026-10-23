"""Тест завантаження версіонованого конфігу експерименту.

verifies: FR-001-03, FR-001-11
"""

import pytest

from itb.config import ConfigError, load


def valid_dict():
    return {
        "config_version": "2026.10.23.1",
        "spend_cap_lamports": 50_000_000,
        "base_fee_lamports": 5000,
        "batch": {"tx_per_batch": 10, "cu_limit": 200_000, "cu_price_lamports": 0},
        "validators": [
            {
                "identity": "TestValidator1111111111111111111111111111111111",
                "label": "agave-1",
                "expected_client": "agave",
            }
        ],
        "rpc": {"http_url_ref": "env:RPC_URL", "ws_url_ref": "env:WS_URL"},
    }


def test_load_valid_dict():
    cfg = load(valid_dict())
    assert cfg.config_version == "2026.10.23.1"
    assert cfg.spend_cap_lamports == 50_000_000
    assert len(cfg.validators) == 1


def test_zero_cap_allowed_means_forbid_live():
    d = valid_dict()
    d["spend_cap_lamports"] = 0
    cfg = load(d)
    assert cfg.spend_cap_lamports == 0


def test_missing_spend_cap_fails_with_field():
    d = valid_dict()
    del d["spend_cap_lamports"]
    with pytest.raises(ConfigError) as e:
        load(d)
    assert "spend_cap_lamports" in str(e.value)


def test_missing_version_fails():
    d = valid_dict()
    del d["config_version"]
    with pytest.raises(ConfigError):
        load(d)


def test_tx_per_batch_out_of_range_fails():
    for bad in (0, 7, 13, 100):
        d = valid_dict()
        d["batch"]["tx_per_batch"] = bad
        with pytest.raises(ConfigError):
            load(d)


def test_url_instead_of_env_ref_fails():
    d = valid_dict()
    d["rpc"]["http_url_ref"] = "https://mainnet.example/rpc"
    with pytest.raises(ConfigError):
        load(d)


def test_empty_validators_fails():
    d = valid_dict()
    d["validators"] = []
    with pytest.raises(ConfigError):
        load(d)
