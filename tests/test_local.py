"""Тест локального профілю: парсинг фікстури блока, compose без mainnet.

verifies: FR-001-12
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_verify():
    spec = importlib.util.spec_from_file_location("verify_mod", ROOT / "scripts" / "verify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixture_block_parses_to_positions(tmp_path):
    verify = load_verify()
    fixture = ROOT / "tests" / "fixtures" / "block_100.json"
    assert fixture.is_file(), "фікстура блока відсутня"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    (tmp_path / "blocks").mkdir(parents=True, exist_ok=True)
    (tmp_path / "blocks" / "100.json").write_text(json.dumps(payload), encoding="utf-8")
    sigs = verify.load_block_sigs(tmp_path, 100)
    assert sigs == ["sig0", "sig1", "sig2", "sig3", "sig4"]
    assert sigs.index("sig3") == 3


def test_compose_local_profile_has_no_mainnet():
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "local-validator" in text
    assert "profiles" in text and "local" in text
    low = text.lower()
    assert "api.mainnet" not in low and "mainnet-beta" not in low
    assert "solana-test-validator" in low
