# impl: FR-002-09
"""Збір позицій наших tx з getBlock у порядку entries.

fetch: callable(slot) -> block-dict | None (None = пропущений слот).
"""

from __future__ import annotations

import csv
from pathlib import Path

from . import storage as _storage


def _sigs_in_order(block: dict) -> list:
    return [t.get("signature") if isinstance(t, dict) else t
            for t in block.get("transactions", [])]


def collect(data_dir, fetch) -> list:
    """Прочитати sent.csv, зібрати landed.csv + blocks/. Повернути записи."""
    data_dir = Path(data_dir)
    out = []
    with (data_dir / "sent.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            slot = int(row["target_slot"])
            sig = row["signature"]
            block = fetch(slot)
            if block is None:
                rec = {"signature": sig, "slot": slot, "position": -1,
                       "batch_id": row.get("batch_id", ""), "idx": row.get("idx", ""),
                       "status": "missing"}
            else:
                _storage.save_block(data_dir, slot, block)
                sigs = _sigs_in_order(block)
                if sig in sigs:
                    rec = {"signature": sig, "slot": slot, "position": sigs.index(sig),
                           "batch_id": row.get("batch_id", ""), "idx": row.get("idx", ""),
                           "status": "landed"}
                else:
                    rec = {"signature": sig, "slot": slot, "position": -1,
                           "batch_id": row.get("batch_id", ""), "idx": row.get("idx", ""),
                           "status": "missing"}
            out.append(rec)
    _storage.write_landed(data_dir, out)
    return out
