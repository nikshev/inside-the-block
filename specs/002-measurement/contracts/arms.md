# Contract: arms (FR-002-04/05)

`build_arm_batch(arm, seed, levels, cfg) -> ArmBatch` (`python/itb/arms.py`).

| Рукав | levels | CU price | CU limit | Платники | Writable |
|---|---|---|---|---|---|
| A | N цін | різні | фікс | пул N незалежних | — |
| B | порядок/інтервал | однаковий | фікс | пул незалежних | — |
| C | N лімітів | фіксований | різні | пул незалежних | — |
| D | N цін (як A) | різні | фікс | один спільний | спільний акаунт |

Перестановка `send_order` — Fisher–Yates з `random.Random(seed)`; seed у лог
і `sent.csv`. Інваріанти перевіряються тестом на кожен рукав.
