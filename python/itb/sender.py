# impl: FR-002-07
"""Транспорти відправки: реальний RPC-шлях і TPU-заглушка.

Реальний QUIC на TPU — операційне рішення після виміру landing rate;
DirectTpuStub фіксує шлях у даних і нічого не відправляє.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.request


class RpcSender:
    """sendTransaction через JSON-RPC (staked sender провайдера)."""

    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url

    def send(self, txs: list, batch_id: str, idx_offset: int = 0) -> list:
        """Відправити tx по черзі send_order; повернути SendRecord-и."""
        recs = []
        for i, t in enumerate(txs):
            sent_at_us = time.time_ns() // 1000
            req = {
                "jsonrpc": "2.0",
                "id": f"{batch_id}:{i}",
                "method": "sendTransaction",
                "params": [
                    base64.b64encode(t["wire"]).decode(),
                    {"skipPreflight": True, "maxRetries": 0, "encoding": "base64"},
                ],
            }
            data = json.dumps(req).encode()
            http_req = urllib.request.Request(
                self.rpc_url, data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(http_req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
            if result.get("error"):
                raise RuntimeError(f"sendTransaction: {result['error']}")
            recs.append(
                {
                    "batch_id": batch_id,
                    "idx": idx_offset + i,
                    "signature_b58": t.get("signature_b58", ""),
                    "sent_at_us": sent_at_us,
                    "path": "rpc",
                    "target_slot": t.get("target_slot"),
                    "tx_signature": result.get("result"),
                }
            )
        return recs


class DirectTpuStub:
    """Заглушка прямого TPU/QUIC: нічого не відправляє, шлях пишеться як змінна."""

    def send(self, txs: list, batch_id: str, idx_offset: int = 0) -> list:
        return [
            {
                "batch_id": batch_id,
                "idx": idx_offset + i,
                "signature_b58": t.get("signature_b58", ""),
                "sent_at_us": time.time_ns() // 1000,
                "path": "direct-tpu",
                "note": "NOT-CONNECTED",
                "target_slot": t.get("target_slot"),
            }
            for i, t in enumerate(txs)
        ]
