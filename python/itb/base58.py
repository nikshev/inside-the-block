# impl: FR-002-03
"""Base58 (алфавіт Bitcoin/Solana). Чисті функції, тільки stdlib."""

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
INDEX = {c: i for i, c in enumerate(ALPHABET)}


def encode(b: bytes) -> str:
    """Закодувати bytes у base58. Ведучі нульові байти → '1'."""
    n_pad = len(b) - len(b.lstrip(b"\x00"))
    num = int.from_bytes(b, "big")
    out = ""
    while num > 0:
        num, r = divmod(num, 58)
        out = ALPHABET[r] + out
    return "1" * n_pad + out


def decode(s: str) -> bytes:
    """Декодувати base58. Невідомий символ → ValueError."""
    n_pad = len(s) - len(s.lstrip("1"))
    num = 0
    for c in s:
        if c not in INDEX:
            raise ValueError(f"base58: невідомий символ {c!r}")
        num = num * 58 + INDEX[c]
    raw = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""
    return b"\x00" * n_pad + raw
