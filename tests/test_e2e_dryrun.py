"""Наскрізний dry-run на 6 валідаторах-заглушках з experiment.yaml.

verifies: FR-001-01, FR-001-06, FR-001-07, FR-001-11
"""

import csv

from itb.config import load
from itb.pipeline import run
from itb.storage import save_snapshot


def test_e2e_dryrun_six_validators(tmp_path):
    cfg = load("config/experiment.yaml")
    assert len(cfg.validators) >= 6
    logs = []
    data = tmp_path / "data"
    report = run(
        cfg, mode="dry-run", data_dir=data,
        ledger_path=data / "spend_ledger.jsonl",
        emit=lambda r: logs.append(r),
    )
    assert report["mode"] == "dry-run"
    # кожен валідатор або з батчем, або з причиною no-window — у 001 вікна-заглушки для всіх
    assert len(logs) == len(cfg.validators)
    assert all(l["msg"] == "would-stop-before-send" for l in logs)
    assert all(l["config_version"] == cfg.config_version for l in logs)
    assert all("batch_max_lamports" in l for l in logs)  # guard-розрахунок видно

    save_snapshot(data, {"measured_at": "stub", "validators": [v.label for v in cfg.validators]})
    with (data / "sent.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(cfg.validators) * cfg.batch.tx_per_batch
    assert {r["config_version"] for r in rows} == {cfg.config_version}
    assert not (data / "spend_ledger.jsonl").is_file()  # dry-run грошей не чіпає
