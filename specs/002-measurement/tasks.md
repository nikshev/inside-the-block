# Tasks: 002-measurement

**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`

## Phase 1: Криптографія і кодування (critical)

- [ ] T-012 [FR-002-03] critical: base58 encode/decode + вектори. Тест `tests/test_base58.py`. Імпл `python/itb/base58.py`.
- [ ] T-013 [FR-002-02] critical: ed25519 sign/verify + RFC 8032 вектори. Тест `tests/test_ed25519.py`. Імпл `python/itb/ed25519.py` (вендорений еталон, походження в шапці).
- [ ] T-014 [FR-002-01] critical: Серіалізація message/tx + builder Memo+ComputeBudget. Тест `tests/test_txbuilder.py` (детермінований golden bytes для фіксованого входу; кожен підпис верифікується). Імпл `python/itb/txbuilder.py`.

## Phase 2: Дизайн батчів

- [ ] T-015 [FR-002-04, FR-002-05] Генератори рукавів A–D + seed-перестановка. Тест `tests/test_arms.py` (4 інваріанти + відтворюваність за seed). Імпл `python/itb/arms.py`.

## Phase 3: Розклад, відправка, збір

- [ ] T-016 [FR-002-06] Вікна лідера + snapshot версій з фікстур RPC. Тест `tests/test_schedule.py`. Імпл `python/itb/schedule.py`.
- [ ] T-017 [FR-002-07] RpcSender проти локального HTTP-стаба + DirectTpuStub. Тест `tests/test_sender.py` (стаб перевіряє `maxRetries=0`, base64 tx, запис path). Імпл `python/itb/sender.py`.
- [ ] T-018 [FR-002-09] Collector: фікстура 3 слотів/15 tx → точні позиції + missing. Тест `tests/test_collector.py`. Імпл `python/itb/collector.py`.

## Phase 4: Оркестрація батча

- [ ] T-019 [FR-002-08, FR-002-10] critical: `measure.run_batch`: guard→build→sign→verify→send→collect; off-target мітка; dry-run без мережі. Тест `tests/test_measure.py` (dry-run без мережі; off-target виключається; guard-reject зупиняє). Імпл `python/itb/measure.py`.

## Покриття FR

| FR | Задачі |
|---|---|
| FR-002-01 | T-014 |
| FR-002-02 | T-013 |
| FR-002-03 | T-012 |
| FR-002-04 | T-015 |
| FR-002-05 | T-015 |
| FR-002-06 | T-016 |
| FR-002-07 | T-017 |
| FR-002-08 | T-019 |
| FR-002-09 | T-018 |
| FR-002-10 | T-019 |

## Ескалації

Жодної поки.
