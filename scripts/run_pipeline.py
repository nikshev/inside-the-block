"""Entrypoint Docker: MODE=dry-run за замовчуванням, live лише з MODE=live."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from itb import config as C
from itb import pipeline as P

mode = os.environ.get("MODE", "dry-run")
cfg = C.load("config/experiment.yaml")
report = P.run(cfg, mode=mode, data_dir="data", ledger_path="data/spend_ledger.jsonl")
print(report)
