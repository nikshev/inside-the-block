# impl: FR-001-07
"""Потоковий запис сирих даних у фіксованій розкладці data/.

Контракт: specs/001-pipeline-safety/contracts/raw-data.md.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

SENT_FIELDS = (
    "batch_id", "idx", "signature", "memo_tag", "validator_label",
    "cu_limit", "cu_price_lamports", "payer", "sent_at_us", "path",
    "target_slot", "config_version", "stub_signature",
)

LANDED_FIELDS = ("signature", "slot", "position", "batch_id", "idx", "status")


def _append_csv(path: Path, fields, rows: list) -> None:
    new = not path.is_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fields))
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_sent(data_dir, txs: list) -> None:
    """Дописати tx у data/sent.csv з фіксованим заголовком."""
    _append_csv(Path(data_dir) / "sent.csv", SENT_FIELDS, txs)


def write_landed(data_dir, records: list) -> None:
    """Дописати записи у data/landed.csv (status landed|missing)."""
    for r in records:
        if r.get("status") not in ("landed", "missing"):
            raise ValueError(f"storage: bad landed status {r!r}")
    _append_csv(Path(data_dir) / "landed.csv", LANDED_FIELDS, records)


def save_block(data_dir, slot: int, block: dict, encoding: str = "stub") -> None:
    """Зберегти сирий getBlock у data/blocks/<slot>.json."""
    d = Path(data_dir) / "blocks"
    d.mkdir(parents=True, exist_ok=True)
    payload = {"slot": slot, "encoding": encoding, "block": block}
    (d / f"{slot}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def save_snapshot(data_dir, snapshot: dict) -> None:
    """Зберегти знімок версій валідаторів."""
    p = Path(data_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "validators_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
