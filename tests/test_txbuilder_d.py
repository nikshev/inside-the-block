"""Золотий вектор SDK для розкладки з extra writable (рукав D).

Згенеровано solders 2026-10-24 (seed=sha256('inside-the-block golden D batch'),
blockhash=bytes(range(32,64)), limit=200000, price=1000, memo='batchD:5',
extra=['59qzdJyTmTHLoo4kt1RjEBcuh6EnwbRvNJZAgNE3ATn1']).

verifies: FR-002-01
"""

import hashlib

from itb import base58, txbuilder

PAYER_B58 = "7fMpzD5GKLVgqFg6Br66cWNQs9rNy1tUSgU3eFwaYQue"
BLOCKHASH = bytes(range(32, 64))
EXTRA = ["59qzdJyTmTHLoo4kt1RjEBcuh6EnwbRvNJZAgNE3ATn1"]
MSG_HEX = (
    "0100020462f9bdeac625914e8e43691898a10799ed9b72a97b76c21decb01960"
    "fd1b73d13db2ca96d7ea0ae5b400ac6b002026d447c4742c8aa66517acf74905"
    "badd40420306466fe5211732ffecadba72c39be7bc8ce5bbc5f7126b2c439b3a"
    "40000000054a535a992921064d24e87160da387c7c35b5ddbc92bb81e41fa840"
    "4105448d202122232425262728292a2b2c2d2e2f303132333435363738393a3b"
    "3c3d3e3f0302000502400d030002000903e80300000000000003010108626174"
    "6368443a35"
)
SIG_HEX = (
    "a5a8b948cb73ccc9507dcbc3d819fe1d507df6d6d6fa522fffe8f529309d588eb9ce9"
    "e4b190d0572c9717f1e39541a3fbf2f501011cbdc35fec8e4611bf80b03"
)


def test_build_with_extra_matches_sdk():
    payload = txbuilder.build_memo_transfer(
        PAYER_B58, BLOCKHASH, cu_limit=200_000, cu_price=1000,
        memo="batchD:5", extra_writable=EXTRA)
    assert payload.hex() == MSG_HEX


def test_sign_extra_layout_verifies():
    from itb import ed25519
    seed = hashlib.sha256(b"inside-the-block golden D batch").digest()
    sk = seed + ed25519.publickey(seed)
    assert base58.encode(sk[32:]) == PAYER_B58
    sig = txbuilder.sign_payload(bytes.fromhex(MSG_HEX), sk)
    assert sig.hex() == SIG_HEX
    assert txbuilder.verify_signature(bytes.fromhex(MSG_HEX), sig, sk[32:])


def test_empty_extra_matches_legacy_layout():
    payload = txbuilder.build_memo_transfer(
        PAYER_B58, BLOCKHASH, cu_limit=200_000, cu_price=1000,
        memo="batchD:5", extra_writable=[])
    # 3 акаунти замість 4: заголовок кількості відрізняється
    assert payload[3:4] == b"\x03"
