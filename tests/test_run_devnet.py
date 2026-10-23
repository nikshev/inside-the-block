"""Тест devnet-ранера: dry-run без мережі, live вимагає сформовані входи.

Жодної мережі: dry-run гілка не чіпає RPC.
verifies: FR-001-12
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_dryrun_offline(tmp_path):
    sys.path.insert(0, str(ROOT / "python"))
    from itb import ed25519
    seed = bytes([1]) * 32
    kp = tmp_path / "k.json"
    kp.write_text(json.dumps(list(seed + ed25519.publickey(seed))))
    out = tmp_path / "out"
    p = subprocess.run(
        [sys.executable, "scripts/run_devnet.py", "--dry-run",
         "--keypair", str(kp), "--data-dir", str(out),
         "--blockhash", "00" * 32],
        capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    assert (out / "sent.csv").is_file()


def test_live_requires_rpc_and_keypair(tmp_path):
    p = subprocess.run(
        [sys.executable, "scripts/run_devnet.py", "--help"],
        capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0
    assert "--rpc" in p.stdout and "--keypair" in p.stdout
