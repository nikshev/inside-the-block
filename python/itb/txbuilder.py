# impl: FR-002-01
"""Побудова і підпис Solana-транзакцій (Memo + ComputeBudget), тільки stdlib.

Формат звірено з реальним SDK (solders): золотий вектор у
tests/test_txbuilder.py. Правило порядку акаунтів: payer, далі програми в
порядку першої появи в інструкціях (cb, memo) — детерміновано для нашого
фіксованого набору з 3 інструкцій.
"""

from __future__ import annotations

import struct

from . import base58, ed25519

MEMO_PROGRAM_B58 = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"  # spl.memo.MEMO_PROGRAM_ID
COMPUTE_BUDGET_PROGRAM_B58 = "ComputeBudget111111111111111111111111111111"

SET_COMPUTE_UNIT_LIMIT_DISC = 2
SET_COMPUTE_UNIT_PRICE_DISC = 3


def compact_u16(n: int) -> bytes:
    """Short-vec кодування довжини (як у Solana message)."""
    if n < 0:
        raise ValueError("compact_u16: від'ємне")
    out = bytearray()
    v = n
    while True:
        b = v & 0x7F
        v >>= 7
        out.append(b | (0x80 if v else 0))
        if not v:
            return bytes(out)


def _ix(program_index: int, data: bytes, accounts: list | None = None) -> bytes:
    accs = bytes(accounts or [])
    return (bytes([program_index]) + compact_u16(len(accs)) + accs
            + compact_u16(len(data)) + data)


def build_memo_transfer(
    payer_b58: str, blockhash32: bytes, cu_limit: int, cu_price: int, memo: str,
    extra_writable: list | None = None,
) -> bytes:
    """Серіалізоване повідомлення: payer + [writable...] + cb(limit) + cb(price) + memo.

    extra_writable: список base58-pubkey додаткових WRITABLE акаунтів
    (для рукава D — спільний акаунт створює write-конфлікт у планувальника).
    Порожній за замовчуванням: байти ідентичні історичному формату
    (золотий вектор у tests/test_txbuilder.py).
    """
    if len(blockhash32) != 32:
        raise ValueError("blockhash має бути 32 байти")
    payer = base58.decode(payer_b58)
    cb_prog = base58.decode(COMPUTE_BUDGET_PROGRAM_B58)
    memo_prog = base58.decode(MEMO_PROGRAM_B58)
    extras = [base58.decode(a) for a in (extra_writable or [])]
    memo_bytes = memo.encode("utf-8")

    n_extra = len(extras)
    ix_cb, ix_memo = 1 + n_extra, 2 + n_extra
    header = bytes([1, 0, 2])  # 1 required sig, 0 readonly-signed, 2 readonly-unsigned
    body = (
        header
        + compact_u16(3 + n_extra)
        + payer
        + b"".join(extras)
        + cb_prog
        + memo_prog
        + blockhash32
        + compact_u16(3)
        + _ix(ix_cb, struct.pack("<BI", SET_COMPUTE_UNIT_LIMIT_DISC, cu_limit))
        + _ix(ix_cb, struct.pack("<BQ", SET_COMPUTE_UNIT_PRICE_DISC, cu_price))
        + _ix(ix_memo, memo_bytes, accounts=list(range(1, 1 + n_extra)))
    )
    return body


def sign_payload(payload: bytes, secret_key64: bytes) -> bytes:
    """ed25519-підпис (secret = seed32 || pubkey32)."""
    if len(secret_key64) != 64:
        raise ValueError("secret key має бути 64 байти")
    return ed25519.signature(payload, secret_key64[:32], secret_key64[32:])


def verify_signature(payload: bytes, signature: bytes, pubkey32: bytes) -> bool:
    """Перевірка підпису перед відправкою."""
    return ed25519.checkvalid(signature, payload, pubkey32)


def build_tx_wire(payload: bytes, signature: bytes) -> bytes:
    """Дротовий формат: compact-u16(1) + sig + message."""
    if len(signature) != 64:
        raise ValueError("підпис має бути 64 байти")
    return compact_u16(1) + signature + payload
