# impl: FR-002-08, FR-002-10
"""Оркестрація одного батча: guard → build → sign → verify → send → collect.

Жодної відправки без decide==accepted; dry-run без мережі.
"""

from __future__ import annotations

import time
from pathlib import Path

from . import arms as _arms
from . import base58 as _base58
from . import collector as _collector
from . import guard as _guard
from . import ledger as _ledger
from . import log as _log
from . import storage as _storage
from . import txbuilder as _txb


def run_batch(
    cfg, arm: str, seed: int, levels: list, window: dict,
    blockhash: bytes, keypairs: dict, sender, fetch,
    mode: str, data_dir, ledger_path, actual_leader: str,
    batch_seq: int = 0, emit=None,
) -> dict:
    """Прогнати один батч. Повертає звіт."""
    if mode not in ("dry-run", "live"):
        raise ValueError(f"measure: невідомий mode {mode!r}")
    emit = emit or _log.emit
    data_dir = Path(data_dir)
    batch_id = f"{window.get('label', 'w')}-{arm}-{batch_seq}-{seed}"
    off_target = actual_leader != window.get("validator")
    if mode == "live" and off_target:
        # Вікно чуже: аборт до будь-якої витрати.
        emit({"batch_id": batch_id, "mode": mode, "config_version": cfg.config_version,
              "msg": "off-target-abort", "path": "none"})
        return {"batch_id": batch_id, "mode": mode, "off_target": True,
                "excluded_from_analysis": True, "sent": 0, "signed": 0,
                "verified": 0, "decision": "off-target"}

    spec = _arms.build_arm_batch(arm, seed, levels,
                                 {"tx_per_batch": cfg.batch.tx_per_batch,
                                  "cu_limit": cfg.batch.cu_limit})
    n = len(spec["txs"])
    max_price = max(t["cu_price_lamports"] for t in spec["txs"])
    bmax = _guard.batch_max_lamports(n, cfg.base_fee_lamports, max_price)

    if mode == "live":
        spent = _ledger.spent_total(ledger_path) if Path(ledger_path).is_file() else 0
        ok, reason = _guard.decide(cfg.spend_cap_lamports, spent, bmax)
        if not ok:
            _ledger.append(ledger_path, {
                "batch_id": batch_id, "decided_at": "2026-10-23T00:00:00Z",
                "config_version": cfg.config_version, "batch_max_lamports": bmax,
                "spent_before": spent, "spent_after": spent,
                "decision": "rejected", "reason": reason})
            return {"batch_id": batch_id, "mode": mode, "off_target": off_target,
                    "excluded_from_analysis": off_target, "sent": 0,
                    "signed": 0, "verified": 0, "decision": reason}
    else:
        spent, ok, reason = 0, True, "dry-run"

    # Build + sign + verify (порядок відправки — send_order).
    signed = []
    for pos, idx in enumerate(spec["send_order"]):
        t = spec["txs"][idx]
        payload = _txb.build_memo_transfer(
            _base58.encode(_pubkey_bytes(keypairs, t["payer"])),
            blockhash, t["cu_limit"], t["cu_price_lamports"],
            f"{batch_id}:{t['idx']}")
        sk = keypairs[t["payer"]]
        sig = _txb.sign_payload(payload, sk)
        assert _txb.verify_signature(payload, sig, sk[32:]), "підпис не верифікується"
        signed.append({"wire": _txb.build_tx_wire(payload, sig),
                       "signature_b58": _base58.encode(sig),
                       "target_slot": window["start_slot"],
                       "sent_at_us": time.time_ns() // 1000,
                       "batch_id": batch_id, "idx": t["idx"],
                       "cu_price_lamports": t["cu_price_lamports"],
                       "cu_limit": t["cu_limit"], "payer": t["payer"],
                       "seed": seed, "path": "stub-local",
                       "config_version": cfg.config_version})
    sent_rows = [{
        "batch_id": batch_id, "idx": s["idx"], "signature": s["signature_b58"],
        "memo_tag": f"{batch_id}:{s['idx']}", "validator_label": window.get("label", ""),
        "cu_limit": s["cu_limit"], "cu_price_lamports": s["cu_price_lamports"],
        "payer": s["payer"], "sent_at_us": s["sent_at_us"], "path": "stub-local",
        "target_slot": s["target_slot"], "config_version": cfg.config_version,
        "stub_signature": False} for s in signed]
    _storage.write_sent(data_dir, sent_rows)

    if mode == "dry-run":
        emit({"batch_id": batch_id, "mode": mode, "config_version": cfg.config_version,
              "msg": "would-stop-before-send", "batch_max_lamports": bmax,
              "path": "stub-local"})
        return {"batch_id": batch_id, "mode": mode, "off_target": off_target,
                "excluded_from_analysis": off_target, "sent": 0,
                "signed": len(signed), "verified": len(signed), "decision": reason}

    recs = sender(signed, batch_id=batch_id, idx_offset=0)
    _ledger.append(ledger_path, {
        "batch_id": batch_id, "decided_at": "2026-10-23T00:00:00Z",
        "config_version": cfg.config_version, "batch_max_lamports": bmax,
        "spent_before": spent, "spent_after": spent + bmax,
        "decision": "accepted", "reason": reason})
    for r in recs:
        emit({"batch_id": batch_id, "mode": mode, "config_version": cfg.config_version,
              "msg": "live-sent", "path": r.get("path", "?")})
    landed = _collector.collect(data_dir, fetch)
    return {"batch_id": batch_id, "mode": mode, "off_target": off_target,
            "excluded_from_analysis": off_target, "sent": len(recs),
            "signed": len(signed), "verified": len(signed),
            "decision": reason, "landed": len(landed)}


def _pubkey_bytes(keypairs: dict, payer: str) -> bytes:
    sk = keypairs[payer]
    return sk[32:]
