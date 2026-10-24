"""Тест sender: RpcSender проти локального стаба, TPU-заглушка.

Жодної зовнішньої мережі — http.server на localhost.
verifies: FR-002-07
"""

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from itb.sender import DirectTpuStub, RpcSender


class StubHandler(BaseHTTPRequestHandler):
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        StubHandler.seen.append(body)
        assert body["method"] == "sendTransaction"
        params, opts = body["params"][0], body["params"][1]
        assert opts.get("skipPreflight") is True
        assert opts.get("maxRetries") == 0
        assert opts.get("encoding") == "base64"  # wire у base64, інакше нода відхилить
        base64.b64decode(params)  # валідний base64
        payload = json.dumps({"jsonrpc": "2.0", "id": body["id"],
                              "result": "sigSTUB"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):
        pass


def run_stub():
    srv = HTTPServer(("127.0.0.1", 0), StubHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_rpc_sender_records_path_and_timestamp():
    srv = run_stub()
    try:
        s = RpcSender(f"http://127.0.0.1:{srv.server_port}")
        recs = s.send([{"wire": b"\x01fake-tx-bytes", "signature_b58": "s1",
                        "target_slot": 100}], batch_id="b1", idx_offset=0)
        assert recs[0]["path"] == "rpc"
        assert recs[0]["target_slot"] == 100
        assert isinstance(recs[0]["sent_at_us"], int)
        assert recs[0]["signature_b58"] == "s1"
    finally:
        srv.shutdown()


def test_rpc_error_raises_instead_of_silent_drop():
    class ErrHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            ln = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(ln))
            payload = json.dumps({"jsonrpc": "2.0", "id": body["id"],
                                  "error": {"code": -32602, "message": "bad"}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(payload.__len__()))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), ErrHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        import pytest
        s = RpcSender(f"http://127.0.0.1:{srv.server_port}")
        with pytest.raises(RuntimeError):
            s.send([{"wire": b"x", "signature_b58": "s1", "target_slot": 1}],
                   batch_id="b", idx_offset=0)
    finally:
        srv.shutdown()


def test_direct_tpu_stub_sends_nothing():
    s = DirectTpuStub()
    recs = s.send([{"wire": b"x", "signature_b58": "s9", "target_slot": 7}],
                  batch_id="b9", idx_offset=0)
    assert recs[0]["path"] == "direct-tpu"
    assert recs[0]["note"] == "NOT-CONNECTED"
