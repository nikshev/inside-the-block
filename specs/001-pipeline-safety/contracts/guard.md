# Contract: guard

## Формула (єдина для всього конвеєра)

```
batch_max = len(txs) * base_fee_lamports + sum(tx.cu_price_lamports * tx.cu_limit / 1_000_000 micro-lamport units → lamports, округлення вгору)
```

У 001 `cu_price` з конфігу однаковий для батча-заглушки, тому
`batch_max = N * (base_fee + priority_fee_per_tx)`. Реальна формула
винагороди/CU для аналізу — у 003; тут лише верхня межа витрат.

## Функція

`decide(cap, spent, batch_max) -> (accepted: bool, reason: str)`
(`python/itb/guard.py`, `impl: FR-001-04`, `critical:`):

| Вхід | `accepted` | `reason` |
|---|---|---|
| `batch_max <= 0` або батч порожній | `False` | `empty-batch` |
| `cap == 0` | `False` | `cap-zero` |
| `spent + batch_max <= cap` | `True` | `ok` |
| інакше | `False` | `exceeds-cap` |

Чиста функція: жодних файлів, жодної мережі, жодного часу. Усі межові
випадки (`spent+max == cap` → прийняти; `== cap+1` → відхилити) покриті
тестом `tests/test_guard.py` (`verifies: FR-001-04`).
