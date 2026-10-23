# impl: FR-002-02
"""Ed25519: підпис і перевірка, тільки stdlib.

Вендорена еталонна реалізація за RFC 8032 (конструкція djb, порт із
публічного надбання; формули звірені з RFC 8032 §5.1). Тест — золотий вектор,
згенерований незалежною реалізацією (cryptography), див. tests/test_ed25519.py.
"""

import hashlib

b = 256
q = (1 << 255) - 19
l = (1 << 252) + 27742317777372353535851937790883648493


def H(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def expmod(base: int, exp: int, mod: int) -> int:
    if exp == 0:
        return 1
    t = expmod(base, exp // 2, mod) ** 2 % mod
    if exp & 1:
        t = t * base % mod
    return t


def inv(x: int) -> int:
    return expmod(x, q - 2, q)


d = (-121665 * inv(121666)) % q
I = expmod(2, (q - 1) // 4, q)


def xrecover(y: int) -> int:
    xx = (y * y - 1) * inv(d * y * y + 1)
    x = expmod(xx, (q + 3) // 8, q)
    if (x * x - xx) % q != 0:
        x = (x * I) % q
    if x % 2 != 0:
        x = q - x
    return x


By = (4 * inv(5)) % q
Bx = xrecover(By)
B = [Bx % q, By % q]


def edwards(P, Q):
    # Додавання на скрученій кривій a*x^2+y^2=1+d*x^2*y^2 з a=-1
    # (Hisil–Wong–Carter–Dawson): y3 = (y1*y2 - a*x1*x2)/(1 - d*...).
    x1, y1 = P
    x2, y2 = Q
    x3 = (x1 * y2 + x2 * y1) * inv(1 + d * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * inv(1 - d * x1 * x2 * y1 * y2)
    return [x3 % q, y3 % q]


def scalarmult(P, e: int):
    if e == 0:
        return [0, 1]
    Q = scalarmult(P, e // 2)
    Q = edwards(Q, Q)
    if e & 1:
        Q = edwards(Q, P)
    return Q


def encodeint(y: int) -> bytes:
    bits = [(y >> i) & 1 for i in range(b)]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(b // 8))


def encodepoint(P) -> bytes:
    x, y = P
    bits = [(y >> i) & 1 for i in range(b - 1)] + [x & 1]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(b // 8))


def bit(h: bytes, i: int) -> int:
    return (h[i // 8] >> (i % 8)) & 1


def publickey(sk: bytes) -> bytes:
    h = H(sk)
    a = 2 ** (b - 2) + sum(2**i * bit(h, i) for i in range(3, b - 2))
    return encodepoint(scalarmult(B, a))


def Hint(m: bytes) -> int:
    h = H(m)
    return sum(2**i * bit(h, i) for i in range(2 * b))


def signature(m: bytes, sk: bytes, pk: bytes) -> bytes:
    h = H(sk)
    a = 2 ** (b - 2) + sum(2**i * bit(h, i) for i in range(3, b - 2))
    r = Hint(bytes(h[i] for i in range(b // 8, b // 4)) + m)
    R = scalarmult(B, r)
    S = (r + Hint(encodepoint(R) + pk + m) * a) % l
    return encodepoint(R) + encodeint(S)


def isoncurve(P) -> bool:
    x, y = P
    return (-x * x + y * y - 1 - d * x * x * y * y) % q == 0


def decodeint(s: bytes) -> int:
    return sum(2**i * bit(s, i) for i in range(b))


def decodepoint(s: bytes):
    y = sum(2**i * bit(s, i) for i in range(b - 1))
    sign = bit(s, b - 1)
    x = xrecover(y)
    if x & 1 != sign:
        x = q - x
    P = [x, y]
    if not isoncurve(P):
        raise ValueError("ed25519: точка не на кривій")
    return P


def checkvalid(s: bytes, m: bytes, pk: bytes) -> bool:
    """True якщо підпис валідний, інакше False (не кидає на підробці)."""
    if len(s) != b // 4:
        raise ValueError("ed25519: довжина підпису не 64")
    if len(pk) != b // 8:
        raise ValueError("ed25519: довжина ключа не 32")
    try:
        R = decodepoint(s[: b // 8])
        A = decodepoint(pk)
    except ValueError:
        return False
    S = decodeint(s[b // 8 :])
    h = Hint(encodepoint(R) + pk + m)
    P1 = scalarmult(B, S)
    P2 = edwards(R, scalarmult(A, h))
    return P1 == P2
