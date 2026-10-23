# impl: FR-001-06
"""Структурований JSON-лог: один об'єкт на рядок, stdout.

Контракт: specs/001-pipeline-safety/contracts/log-record.md.
"""

from __future__ import annotations

import json
import sys
import time

REQUIRED = ("batch_id", "mode", "config_version", "msg")


def emit(record: dict, stream=None) -> None:
    """Дописати ts_us, перевірити обов'язкові поля, вивести JSON-рядок."""
    missing = [k for k in REQUIRED if k not in record]
    if missing:
        raise ValueError(f"log: бракує полів {missing}")
    out = dict(record)
    out.setdefault("ts_us", time.time_ns() // 1000)
    out.setdefault("level", "INFO")
    (stream or sys.stdout).write(json.dumps(out, ensure_ascii=False) + "\n")
