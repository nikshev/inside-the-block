# Матриця трасування

<!-- ГЕНЕРУЄТЬСЯ scripts/trace.py — не редагувати вручну -->

Вимог: **22** · задач: **19** (виконано 15) · вимог у роботі: **5** · порушень: **0**

## 001-pipeline-safety

| Вимога | Опис | Задачі | Імплементація | Тести |
|---|---|---|---|---|
| `FR-001-01` | Система MUST запускатися однією командою `docker compose up` | `T-006`, `T-011` | `python/itb/pipeline.py` | `tests/test_pipeline.py`, `tests/test_e2e_dryrun.py` |
| `FR-001-02` | Система MUST відправляти на mainnet лише з явним прапорцем | `T-006` | `python/itb/pipeline.py` | `tests/test_pipeline.py` |
| `FR-001-03` | Система MUST тримати весь ліміт витрат в одному YAML під git | `T-001` | `python/itb/config.py` | `tests/test_config.py` |
| `FR-001-04` | Spend guard MUST до кожної відправки рахувати максимальну | `T-002`, `T-007` | `python/itb/guard.py` | `tests/test_spend_integration.py`, `tests/test_guard.py` |
| `FR-001-05` | Система MUST вести леджер витрат у файлі (append-only) | `T-003`, `T-007` | `python/itb/ledger.py` | `tests/test_spend_integration.py`, `tests/test_ledger.py` |
| `FR-001-06` | Система MUST писати структуровані JSON-логи кожного кроку з | `T-004`, `T-011` | `python/itb/log.py` | `tests/test_e2e_dryrun.py`, `tests/test_log.py` |
| `FR-001-07` | Система MUST зберігати сирі дані у фіксованій розкладці | `T-005`, `T-011` | `python/itb/storage.py` | `tests/test_storage.py`, `tests/test_e2e_dryrun.py` |
| `FR-001-08` | Система MUST надавати скрипт `verify`, що за `data/` заново | `T-008` | `scripts/verify.py` | `tests/test_verify.py` |
| `FR-001-09` | Система MUST тримати ключі лише через volume і RPC URL лише | `T-009` | `docker-compose.yml` | `tests/test_secrets.py` |
| `FR-001-10` | Секрет випадково потрапив у репо: CI-чек падає до мержу (див. ). | `T-009` | `.github/workflows/ci.yml` | `tests/test_secrets.py` |
| `FR-001-11` | Конфіг MUST мати `config_version` і кожен прогін MUST писати | `T-001`, `T-011` | `python/itb/config.py` | `tests/test_config.py`, `tests/test_e2e_dryrun.py` |
| `FR-001-12` | Система MUST підтримувати локальний профіль | `T-010` | `docker-compose.yml` | `tests/test_local.py` |

## 002-measurement

| Вимога | Опис | Задачі | Імплементація | Тести |
|---|---|---|---|---|
| `FR-002-01` | Система MUST будувати tx з інструкцій ComputeBudget | `T-014` | `python/itb/txbuilder.py` | `tests/test_txbuilder.py` |
| `FR-002-02` | Система MUST підписувати tx справжнім ed25519; вендорена | `T-013` | `python/itb/ed25519.py` | `tests/test_ed25519.py` |
| `FR-002-03` | Система MUST кодувати base58 для адрес/сигнатур; реалізація | `T-012` | `python/itb/base58.py` | `tests/test_base58.py` |
| `FR-002-04` | Система MUST реалізовувати рукави A–D за таблицею PRD | `T-015` | `python/itb/arms.py` | `tests/test_arms.py` |
| `FR-002-05` | Порядок відправки в батчі MUST рандомізуватися з seed, що | `T-015` | `python/itb/arms.py` | `tests/test_arms.py` |
| `FR-002-06` | Система MUST читати leader-розклад (`getLeaderSchedule`) і | `T-016` | — | — |
| `FR-002-07` | Відправка MUST підтримувати шлях `direct-tpu` (інтерфейс + | `T-017` | — | — |
| `FR-002-08` | Час відправки кожної tx MUST фіксуватися в мікросекундах; | `T-019` | — | — |
| `FR-002-09` | Збір позицій MUST парсити `getBlock` у порядку entries і | `T-018` | — | — |
| `FR-002-10` | Жодна відправка MUST НЕ відбуватися без `decide==accepted` | `T-019` | — | — |

## Критичні задачі

- `T-001` (001-pipeline-safety) — виконано
- `T-002` (001-pipeline-safety) — виконано
- `T-003` (001-pipeline-safety) — виконано
- `T-007` (001-pipeline-safety) — виконано
- `T-008` (001-pipeline-safety) — виконано
- `T-012` (002-measurement) — виконано
- `T-013` (002-measurement) — виконано
- `T-014` (002-measurement) — виконано
- `T-019` (002-measurement) — у роботі
