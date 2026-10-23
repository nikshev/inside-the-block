"""Тест серіалізації Solana-tx: золотий вектор реального SDK.

Згенеровано 2026-10-23 через solders (Message.new_with_blockhash +
Transaction, seed=sha256('inside-the-block golden payer'),
blockhash=bytes(range(32)), limit=200000, price=1000, memo='batch7:3').

verifies: FR-002-01
"""

import hashlib
import struct

from itb import base58, ed25519, txbuilder

PAYER_B58 = "Fc9VcUrwiUqtaWRH3ao9SJYtuT54D5Y3cZm1RpcHcHUU"
BLOCKHASH = bytes(range(32))
MSG_HEX = (
    "01000203d9048c7777a45d56dce4557de03a480ee721eb8e29d07e7ea175a3125c97a391"
    "0306466fe5211732ffecadba72c39be7bc8ce5bbc5f7126b2c439b3a40000000054a535a99"
    "2921064d24e87160da387c7c35b5ddbc92bb81e41fa8404105448d00010203040506070809"
    "0a0b0c0d0e0f101112131415161718191a1b1c1d1e1f0301000502400d030001000903e803"
    "0000000000000200086261746368373a33"
)
SIG_HEX = (
    "9cd22493fdbdae36178ce1b5f162a5db4d8a07876a03e4d046add38a49c1178d170be5796"
    "81499a5a1db946441ca6d48b84acceb8e43e329a311f163d6c3d204"
)
SEED = hashlib.sha256(b"inside-the-block golden payer").digest()


def test_build_matches_sdk_bytes():
    payload = txbuilder.build_memo_transfer(
        PAYER_B58, BLOCKHASH, cu_limit=200_000, cu_price=1000, memo="batch7:3"
    )
    assert payload.hex() == MSG_HEX


def test_signature_matches_sdk_and_verifies():
    payload = bytes.fromhex(MSG_HEX)
    sk = SEED + ed25519.publickey(SEED)
    sig = txbuilder.sign_payload(payload, sk)
    assert sig.hex() == SIG_HEX
    assert txbuilder.verify_signature(payload, sig, base58.decode(PAYER_B58))


def test_compact_u16_edges():
    assert txbuilder.compact_u16(0) == b"\x00"
    assert txbuilder.compact_u16(127) == b"\x7f"
    assert txbuilder.compact_u16(128) == b"\x80\x01"
    assert txbuilder.compact_u16(16383) == b"\xff\x7f"
    assert txbuilder.compact_u16(16384) == b"\x80\x80\x01"


def test_wire_format():
    payload = bytes.fromhex(MSG_HEX)
    sig = bytes.fromhex(SIG_HEX)
    wire = txbuilder.build_tx_wire(payload, sig)
    assert wire == b"\x01" + sig + payload
    assert struct.unpack("<B", wire[:1])[0] == 1
