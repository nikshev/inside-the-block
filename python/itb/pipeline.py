# impl: FR-001-01, FR-001-02
"""Оркестратор: dry-run будує батчі і зупиняється до sender; live йде через guard.

У 001 live-відправка — виклик ін'єктованого sender (у Docker його немає,
тому реальних витрат бути не може). Реальний TPU/QUIC-сендер — у 002.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from . import guard as _guard
from . import ledger as _ledger
from . import log as _log
from . import storage as _storage


def stub_signature(payload: bytes, payer: str) -> str:
    """Детермінована заглушка підпису. Поле stub_signature=true всюди."""
    return hashlib.sha256(payload + b"|" + payer.encode()).hexdigest()


def build_batch(cfg, validator_label: str, batch_id: str, target_slot: int, sent_at_us: int) -> list:
    """Побудувати tx-заглушки батча: Memo batch_id:idx, CU з конфігу."""
    txs = []
    n = cfg.batch.tx_per_batch
    for idx in range(n):
        payer = f"payer-pool-{idx % 4}"
        memo = f"{batch_id}:{idx}"
        payload = f"{memo}|{cfg.batch.cu_limit}|{cfg.batch.cu_price_lamports}|{payer}".encode()
        txs.append(
            {
                "batch_id": batch_id,
                "idx": idx,
                "signature": stub_signature(payload, payer),
                "memo_tag": memo,
                "validator_label": validator_label,
                "cu_limit": cfg.batch.cu_limit,
                "cu_price_lamports": cfg.batch.cu_price_lamports,
                "payer": payer,
                "sent_at_us": sent_at_us,
                "path": "stub-local",
                "target_slot": target_slot,
                "config_version": cfg.config_version,
                "stub_signature": True,
            }
        )
    return txs


def _batch_max(cfg, txs: list) -> int:
    return _guard.batch_max_lamports(len(txs), cfg.base_fee_lamports, cfg.batch.cu_price_lamports)


def run(cfg, mode: str, data_dir, ledger_path, sender=None, emit=None) -> dict:
    """Прогнати всіх валідаторів конфігу. Повертає звіт {mode, accepted, rejected}."""
    if mode not in ("dry-run", "live"):
        raise ValueError(f"pipeline: невідомий mode {mode!r} (дозволено dry-run|live)")
    emit = emit or _log.emit
    data_dir = Path(data_dir)
    spent = _ledger.spent_total(ledger_path) if Path(ledger_path).is_file() else 0
    accepted = rejected = 0
    for i, v in enumerate(cfg.validators):
        batch_id = f"dry-{v.label}-{i}"
        txs = build_batch(cfg, v.label, batch_id, 100 + i, time.time_ns() // 1000)
        bmax = _batch_max(cfg, txs)
        if mode == "dry-run":
            emit(
                {
                    "batch_id": batch_id,
                    "mode": mode,
                    "config_version": cfg.config_version,
                    "msg": "would-stop-before-send",
                    "batch_max_lamports": bmax,
                    "path": "stub-local",
                }
            )
            _storage.write_sent(data_dir, txs)
            continue
        ok, reason = _guard.decide(cfg.spend_cap_lamports, spent, bmax)
        if ok:
            if sender is not None:
                sender(txs)
            spent_after = spent + bmax
            accepted += 1
        else:
            spent_after = spent
            rejected += 1
        _ledger.append(
            ledger_path,
            {
                "batch_id": batch_id,
                "decided_at": "2026-10-23T00:00:00Z",
                "config_version": cfg.config_version,
                "batch_max_lamports": bmax,
                "spent_before": spent,
                "spent_after": spent_after,
                "decision": "accepted" if ok else "rejected",
                "reason": reason,
            },
        )
        emit(
            {
                "batch_id": batch_id,
                "mode": mode,
                "config_version": cfg.config_version,
                "msg": f"live-{reason}",
                "path": "stub-local",
            }
        )
        spent = spent_after
        _storage.write_sent(data_dir, txs)
    return {"mode": mode, "accepted": accepted, "rejected": rejected}
