"""Тест verify --live-check проти локального RPC-стаба.

verifies: FR-004-03
"""

import csv
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def write_data(root: Path):
    (root / "blocks").mkdir(parents=True, exist_ok=True)
    with (root / "landed.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["signature", "slot", "position",
                                          "batch_id", "idx", "status"])
        w.writeheader()
        w.writerow({"signature": "sigA", "slot": 100, "position": 0,
                    "batch_id": "b", "idx": 0, "status": "landed"})
        w.writerow({"signature": "sigB", "slot": 100, "position": 2,
                    "batch_id": "b", "idx": 1, "status": "landed"})
    (root / "blocks" / "100.json").write_text(
        json.dumps({"slot": 100, "encoding": "stub",
                    "block": {"transactions": [{"signature": "sigA"},
                                              {"signature": "junk"},
                                              {"signature": "sigB"}]}}),
        encoding="utf-8")


CHAIN = {"transactions": [{"signature": "sigA"}, {"signature": "junk"},
                          {"signature": "sigB"}]}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        ln = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(ln))
        assert body["method"] == "getBlock"
        payload = json.dumps({"jsonrpc": "2.0", "id": body["id"],
                              "result": CHAIN}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):
        pass


def run_live(root: Path, port: int):
    return subprocess.run(
        [sys.executable, "scripts/verify.py", str(root),
         "--live-check", "--rpc", f"http://127.0.0.1:{port}"],
        capture_output=True, text=True)


def test_live_check_match(tmp_path):
    write_data(tmp_path)
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        p = run_live(tmp_path, srv.server_port)
    finally:
        srv.shutdown()
    assert p.returncode == 0, p.stderr


def test_live_check_mismatch(tmp_path):
    write_data(tmp_path)
    global CHAIN
    CHAIN = {"transactions": [{"signature": "sigB"}, {"signature": "junk"},
                              {"signature": "sigA"}]}  # порядок інший
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        p = run_live(tmp_path, srv.server_port)
    finally:
        srv.shutdown()
        CHAIN = {"transactions": [{"signature": "sigA"}, {"signature": "junk"},
                                  {"signature": "sigB"}]}
    assert p.returncode == 1
    assert "sigA" in (p.stdout + p.stderr)
