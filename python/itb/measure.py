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
    batch_seq: int = 0, emit=None, send_strategy: str = "stream",
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

    # Build + sign + verify — завжди все й одразу (див. prepare_batch).
    # Відправка — лише у fire_batch, щоб ранер міг підписати заздалегідь
    # і вдарити залпом точно у вікно лідера.
    prepared = prepare_batch(cfg, arm, seed, levels, window, blockhash,
                             keypairs, data_dir, batch_seq, emit)
    signed = prepared["signed"]
    bmax = prepared["bmax"]

    if mode == "dry-run":
        emit({"batch_id": prepared["batch_id"], "mode": mode,
              "config_version": cfg.config_version,
              "msg": "would-stop-before-send", "batch_max_lamports": bmax,
              "path": "stub-local"})
        return {"batch_id": prepared["batch_id"], "mode": mode,
                "off_target": off_target,
                "excluded_from_analysis": off_target, "sent": 0,
                "signed": len(signed), "verified": len(signed), "decision": reason}

    return fire_batch(cfg, prepared, sender, fetch, data_dir, ledger_path,
                      emit=emit)


def _sign_verify_one(args) -> bytes:
    """Підписати і верифікувати один payload. Top-level — для multiprocessing."""
    payload, sk = args
    sig = _txb.sign_payload(payload, sk)
    assert _txb.verify_signature(payload, sig, sk[32:]), "підпис не верифікується"
    return sig


def _sign_all(payloads: list, sks: list, jobs: int = 1) -> list:
    """Підписати пакети; jobs>1 — паралельно (порядок зберігається)."""
    if jobs <= 1:
        return [_sign_verify_one((p, s)) for p, s in zip(payloads, sks)]
    import multiprocessing as mp
    with mp.Pool(processes=jobs) as pool:
        return pool.map(_sign_verify_one, list(zip(payloads, sks)))


def _sent_row(window, cfg, batch_id, s):
    return {
        "batch_id": batch_id, "idx": s["idx"], "signature": s["signature_b58"],
        "memo_tag": f"{batch_id}:{s['idx']}", "validator_label": window.get("label", ""),
        "cu_limit": s["cu_limit"], "cu_price_lamports": s["cu_price_lamports"],
        "payer": s["payer"], "sent_at_us": s["sent_at_us"], "path": "stub-local",
        "target_slot": s["target_slot"], "config_version": cfg.config_version,
        "stub_signature": False}


def prepare_batch(cfg, arm, seed, levels, window, blockhash, keypairs,
                  data_dir, batch_seq=0, emit=None, jobs: int = 1) -> dict:
    """Побудувати+підписати+верифікувати батч і записати sent.csv.

    Жодної відправки, жодного леджера, жодної мережі — придатне для dry-run
    і для завчасного підпису перед вікном лідера. jobs>1 — паралельний
    підпис через multiprocessing (той самий байтовий результат).
    """
    emit = emit or _log.emit
    data_dir = Path(data_dir)
    batch_id = f"{window.get('label', 'w')}-{arm}-{batch_seq}-{seed}"
    spec = _arms.build_arm_batch(arm, seed, levels,
                                 {"tx_per_batch": cfg.batch.tx_per_batch,
                                  "cu_limit": cfg.batch.cu_limit})
    n = len(spec["txs"])
    max_price = max(t["cu_price_lamports"] for t in spec["txs"])
    bmax = _guard.batch_max_lamports(n, cfg.base_fee_lamports, max_price)
    payloads, sks = [], []
    for idx in spec["send_order"]:
        t = spec["txs"][idx]
        payloads.append(_txb.build_memo_transfer(
            _base58.encode(_pubkey_bytes(keypairs, t["payer"])),
            blockhash, t["cu_limit"], t["cu_price_lamports"],
            f"{batch_id}:{t['idx']}"))
        sks.append(keypairs[t["payer"]])
    sigs = _sign_all(payloads, sks, jobs=jobs)
    signed = []
    order = spec["send_order"]
    for pos, (idx, sig) in enumerate(zip(order, sigs)):
        t = spec["txs"][idx]
        signed.append({"wire": _txb.build_tx_wire(payloads[pos], sig),
                       "signature_b58": _base58.encode(sig),
                       "target_slot": window["start_slot"],
                       "sent_at_us": time.time_ns() // 1000,
                       "batch_id": batch_id, "idx": t["idx"],
                       "cu_price_lamports": t["cu_price_lamports"],
                       "cu_limit": t["cu_limit"], "payer": t["payer"],
                       "seed": seed, "path": "stub-local",
                       "config_version": cfg.config_version})
    _storage.write_sent(
        data_dir, [_sent_row(window, cfg, batch_id, s) for s in signed])
    return {"batch_id": batch_id, "signed": signed, "bmax": bmax, "spec": spec,
            "window": window, "seed": seed, "arm": arm}


def fire_batch(cfg, prepared: dict, sender, fetch, data_dir, ledger_path,
               emit=None) -> dict:
    """Guard → леджер → відправка по одній у send_order → збір позицій."""
    emit = emit or _log.emit
    data_dir = Path(data_dir)
    batch_id = prepared["batch_id"]
    bmax = prepared["bmax"]
    window = prepared["window"]
    off_target = False  # fire викликається лише після перевірки вікна викликачем
    spent = _ledger.spent_total(ledger_path) if Path(ledger_path).is_file() else 0
    ok, reason = _guard.decide(cfg.spend_cap_lamports, spent, bmax)
    if not ok:
        _ledger.append(ledger_path, {
            "batch_id": batch_id, "decided_at": "2026-10-23T00:00:00Z",
            "config_version": cfg.config_version, "batch_max_lamports": bmax,
            "spent_before": spent, "spent_after": spent,
            "decision": "rejected", "reason": reason})
        return {"batch_id": batch_id, "mode": "live", "off_target": off_target,
                "excluded_from_analysis": off_target, "sent": 0,
                "signed": len(prepared["signed"]), "verified": len(prepared["signed"]),
                "decision": reason}
    recs = []
    for pos, tx in enumerate(prepared["signed"]):
        recs.extend(sender([tx], batch_id=batch_id, idx_offset=pos))
    _ledger.append(ledger_path, {
        "batch_id": batch_id, "decided_at": "2026-10-23T00:00:00Z",
        "config_version": cfg.config_version, "batch_max_lamports": bmax,
        "spent_before": spent, "spent_after": spent + bmax,
        "decision": "accepted", "reason": reason})
    for r in recs:
        emit({"batch_id": batch_id, "mode": "live", "config_version": cfg.config_version,
              "msg": "live-sent", "path": r.get("path", "?")})
    landed = _collector.collect(data_dir, fetch)
    return {"batch_id": batch_id, "mode": "live", "off_target": off_target,
            "excluded_from_analysis": off_target, "sent": len(recs),
            "signed": len(prepared["signed"]), "verified": len(prepared["signed"]),
            "decision": reason, "landed": len(landed)}


def _pubkey_bytes(keypairs: dict, payer: str) -> bytes:
    sk = keypairs[payer]
    return sk[32:]
