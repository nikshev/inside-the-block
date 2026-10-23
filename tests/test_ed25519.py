"""Тест ed25519: золотий вектор незалежної реалізації + roundtrip.

Золотий вектор згенеровано 2026-10-23 локально через
cryptography.Ed25519PrivateKey (ключ = RFC 8032 TEST 1 secret).

verifies: FR-002-02
"""

import os

from itb import ed25519

SK = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
PK = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
MSG = b"inside-the-block golden vector"
SIG = bytes.fromhex(
    "e33c212ea85a74c95de5c142ff5be1c0ed25999aabfa119c1884b5575465e6fdd"
    "990e73a13b38fa67c04dcc2d4d6f348e5727d7179622468c41d80ffbce9e905"
)


def test_publickey_matches_independent():
    assert ed25519.publickey(SK) == PK


def test_signature_matches_independent_deterministic():
    assert ed25519.signature(MSG, SK, PK) == SIG


def test_checkvalid_accepts():
    assert ed25519.checkvalid(SIG, MSG, PK) is True


def test_checkvalid_rejects_tampered():
    bad = bytearray(SIG)
    bad[0] ^= 1
    assert ed25519.checkvalid(bytes(bad), MSG, PK) is False


def test_roundtrip_random_key():
    sk = os.urandom(32)
    pk = ed25519.publickey(sk)
    m = os.urandom(64)
    sig = ed25519.signature(m, sk, pk)
    assert ed25519.checkvalid(sig, m, pk) is True
