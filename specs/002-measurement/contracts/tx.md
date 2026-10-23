# Contract: tx (FR-002-01/02/03)

## Серіалізація повідомлення

```
compact-u16(n) || signatures[] (поза message) ||
header(num_required_signatures=1, num_readonly_signed=0, num_readonly_unsigned=2) ||
account_keys[payer, memo_program, compute_budget_program] ||
recent_blockhash(32B) ||
compact-u16(3 instructions) || ix... ||
```

- `MemoSq4gqAaxu9fRj55s8tK3Pzj6pgXBUxVfBYRg7yJNZ` (Memo program v1).
- ComputeBudget `ComputeBudget111111111111111111111111111111`:
  ix0 = SetComputeUnitLimit(2) + u32 LE; ix1 = SetComputeUnitPrice(3) + u64 LE micro-lamports.
- ix2 = Memo, data = UTF-8 `batch_id:idx`, accounts = [].
- Акаунти: payer (signer+writable), Memo program (readonly), ComputeBudget (readonly).

## Функції (`python/itb/txbuilder.py`, `impl: FR-002-01`)

`build_memo_transfer(payer_b58, blockhash32, cu_limit, cu_price, memo) -> payload_bytes`.
`sign_payload(payload, privkey32) -> signature64` (через `ed25519.py`).

## ed25519 (`python/itb/ed25519.py`, `impl: FR-002-02`)

Вендорений еталон (походження в шапці): `sign(sk, msg)`, `verify(vk, sig, msg)`.
Тест — вектори RFC 8032 (TEST 1..3 + пусте повідомлення).

## base58 (`python/itb/base58.py`, `impl: FR-002-03`)

`encode(b)`, `decode(s)`; ведучі `\x00` → `1`; тест-вектори: `b""→""`,
`b"\x00\x00"→"11"`, відомий адрес системної програми.
