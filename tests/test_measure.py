"""Тест оркестрації батча: guard, підписи, off-target, dry-run без мережі.

verifies: FR-002-08, FR-002-10
"""

from itb import ed25519
from itb.config import load
from itb.measure import run_batch


def make_cfg(cap=50_000_000):
    return load(
        {
            "config_version": "2026.10.23.1",
            "spend_cap_lamports": cap,
            "base_fee_lamports": 5000,
            "batch": {"tx_per_batch": 8, "cu_limit": 200_000, "cu_price_lamports": 0},
            "validators": [{"identity": "V1", "label": "agave-1", "expected_client": "agave"}],
            "rpc": {"http_url_ref": "env:RPC_URL", "ws_url_ref": "env:WS_URL"},
        }
    )


def keypairs():
    out = {}
    for i in range(8):
        seed = bytes([i + 1]) * 32
        out[f"payer-pool-{i}"] = seed + ed25519.publickey(seed)
    out["payer-shared-conflict"] = out["payer-pool-0"]
    return out


def boom(*a, **k):
    raise AssertionError("мережа заборонена в цьому тесті")


def test_dryrun_no_network_signatures_verify(tmp_path):
    report = run_batch(
        make_cfg(), arm="A", seed=11, levels=[0, 100, 500, 1000, 2000, 5000, 10000, 20000],
        window={"validator": "V1", "label": "agave-1", "start_slot": 50, "end_slot": 53},
        blockhash=bytes(range(32)), keypairs=keypairs(), sender=boom, fetch=boom,
        mode="dry-run", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl", actual_leader="V1",
    )
    assert report["signed"] == 8 and report["verified"] == 8
    assert report["sent"] == 0 and report["off_target"] is False


def test_guard_reject_stops_before_build(tmp_path):
    def sender_spy(*a, **k):
        sender_spy.calls += 1
        return []

    sender_spy.calls = 0
    report = run_batch(
        make_cfg(cap=0), arm="A", seed=11, levels=[0, 100, 500, 1000, 2000, 5000, 10000, 20000],
        window={"validator": "V1", "label": "agave-1", "start_slot": 50, "end_slot": 53},
        blockhash=bytes(range(32)), keypairs=keypairs(), sender=sender_spy, fetch=boom,
        mode="live", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl", actual_leader="V1",
    )
    assert report["decision"] == "cap-zero"
    assert sender_spy.calls == 0


def test_live_sends_streaming_in_send_order(tmp_path):
    """Live: sender викликається по одній tx у порядку send_order (без прострочки blockhash)."""
    from itb import arms as A

    cfg = make_cfg()
    calls = []
    spec = A.build_arm_batch("A", 11, [0, 100, 500, 1000, 2000, 5000, 10000, 20000],
                             {"tx_per_batch": 8, "cu_limit": 200_000})
    report = run_batch(
        cfg, arm="A", seed=11, levels=[0, 100, 500, 1000, 2000, 5000, 10000, 20000],
        window={"validator": "V1", "label": "agave-1", "start_slot": 50, "end_slot": 53},
        blockhash=bytes(range(32)), keypairs=keypairs(),
        sender=lambda txs, batch_id, idx_offset: (
            calls.append([t["idx"] for t in txs]),
            [{"path": "stub", "signature_b58": t["signature_b58"]} for t in txs],
        )[1],
        fetch=lambda slot: None, mode="live", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl", actual_leader="V1",
    )
    assert report["sent"] == 8
    flat = [i for c in calls for i in c]
    assert flat == spec["send_order"], "порядок відправки мусить збігатися з send_order"
    assert all(len(c) == 1 for c in calls), "потоково: по одній tx за виклик"


def test_burst_sends_same_order(tmp_path):
    """Burst: усі підписи готові до відправки, порядок той самий."""
    from itb import arms as A

    cfg = make_cfg()
    calls = []
    spec = A.build_arm_batch("B", 5, [100],
                             {"tx_per_batch": 8, "cu_limit": 200_000})
    report = run_batch(
        cfg, arm="B", seed=5, levels=[100],
        window={"validator": "V1", "label": "agave-1", "start_slot": 50, "end_slot": 53},
        blockhash=bytes(range(32)), keypairs=keypairs(),
        sender=lambda txs, batch_id, idx_offset: (
            calls.append([t["idx"] for t in txs]),
            [{"path": "stub", "signature_b58": t["signature_b58"]} for t in txs],
        )[1],
        fetch=lambda slot: None, mode="live", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl", actual_leader="V1",
        send_strategy="burst",
    )
    assert report["sent"] == 8
    assert [i for c in calls for i in c] == spec["send_order"]


def test_parallel_sign_matches_serial(tmp_path):
    """Паралельний підпис дає ті самі байти, що й послідовний."""
    from itb import txbuilder as T

    payloads = [b"probe-payload-%d" % i for i in range(2)]
    seed = bytes([9]) * 32
    from itb import ed25519
    sk = seed + ed25519.publickey(seed)
    from itb.measure import _sign_all
    assert _sign_all(payloads, [sk, sk], jobs=1) == _sign_all(payloads, [sk, sk], jobs=2)


def test_off_target_excluded_from_analysis(tmp_path):
    report = run_batch(
        make_cfg(), arm="B", seed=5, levels=[100],
        window={"validator": "V1", "label": "agave-1", "start_slot": 50, "end_slot": 53},
        blockhash=bytes(range(32)), keypairs=keypairs(), sender=boom, fetch=boom,
        mode="dry-run", data_dir=tmp_path / "data",
        ledger_path=tmp_path / "ledger.jsonl", actual_leader="SOMEONE-ELSE",
    )
    assert report["off_target"] is True
    assert report["excluded_from_analysis"] is True

    calls = []

    def spy(*a, **k):
        calls.append(1)
        return []

    live = run_batch(  # live з off-target: аборт до відправки
        make_cfg(), arm="B", seed=5, levels=[100],
        window={"validator": "V1", "label": "agave-1", "start_slot": 50, "end_slot": 53},
        blockhash=bytes(range(32)), keypairs=keypairs(), sender=spy, fetch=boom,
        mode="live", data_dir=tmp_path / "data2",
        ledger_path=tmp_path / "ledger.jsonl", actual_leader="SOMEONE-ELSE",
    )
    assert live["off_target"] is True and live["sent"] == 0
    assert calls == []
