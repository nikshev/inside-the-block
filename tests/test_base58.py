"""Тест base58 (адреси, сигнатури).

verifies: FR-002-03
"""

import os

from itb.base58 import decode, encode


def test_vectors():
    assert encode(b"") == ""
    assert encode(b"\x00") == "1"
    assert encode(b"\x00\x00") == "11"
    assert encode(b"hello world") == "StV1DL6CwTryKyV"
    assert decode("StV1DL6CwTryKyV") == b"hello world"
    assert decode("11") == b"\x00\x00"


def test_roundtrip_random():
    for _ in range(50):
        b = os.urandom(32)
        assert decode(encode(b)) == b


def test_invalid_char_fails():
    import pytest

    with pytest.raises(ValueError):
        decode("0OIl")  # поза алфавітом
