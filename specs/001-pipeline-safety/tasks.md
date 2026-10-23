# Tasks: 001-pipeline-safety

**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`

**Порядок**: тест першим (червоний з очікуваної причини) → код → `trace.py` → reviewer.
Одна задача — один прохід. `critical:` йде одразу на `implementer-senior`.

## Phase 1: Foundational — конфіг, гроші, логи, дані

Блокери для всього іншого. Порядок всередині фази — за залежностями.

- [x] T-001 [FR-001-03, FR-001-11] critical: Конфіг-лоадер + приклад YAML. Тест `tests/test_config.py` (dict без pyyaml: валідний конфіг грузиться, відсутній `spend_cap` / невідома версія / URL замість `env:` — падає з полем помилки). Імпл `python/itb/config.py` + `config/experiment.yaml`. Контракт `contracts/config.md`.
- [x] T-002 [FR-001-04] critical: Spend guard як чиста функція. Тест `tests/test_guard.py` (межі: `spent+max==cap` прийняти, `==cap+1` відхилити, `cap==0` відхилити, порожній батч відхилити). Імпл `python/itb/guard.py`. Контракт `contracts/guard.md`.
- [ ] T-003 [FR-001-05] critical: Append-only леджер з відновленням. Тест `tests/test_ledger.py` (append accepted/rejected → `spent_total` збігається після перевідкриття; інваріант `spent_after ≤ cap`). Імпл `python/itb/ledger.py`. Контракт `contracts/ledger.md`.
- [ ] T-004 [FR-001-06] JSON-логер. Тест `tests/test_log.py` (обов'язкові поля, `ts_us` int, жодних секретів у виводі). Імпл `python/itb/log.py`. Контракт `contracts/log-record.md`.
- [ ] T-005 [FR-001-07] Сховище сирих даних. Тест `tests/test_storage.py` (запис `sent.csv`/`landed.csv` з фіксованим заголовком + `save_block`/`save_snapshot`; `missing` слот окремо). Імпл `python/itb/storage.py`. Контракт `contracts/raw-data.md`.

**Checkpoint**: фундамент готовий — guard тримає гроші, формати зафіксовані.

## Phase 2: User Story 1 — Dry-run однією командою (P1)

Незалежний тест: `docker compose up` без ключів → exit 0, `mode=dry-run`,
`spend_guard=would-stop-before-send`, леджер порожній, жодної відправки.

- [ ] T-006 [FR-001-01, FR-001-02] Pipeline-оркестратор + Docker. Тест `tests/test_pipeline.py` (dry-run будує батч із stub-підписами і зупиняється до sender; `MODE=live` без guard падає; логи містять `mode`+`config_version`). Імпл `python/itb/pipeline.py` + `Dockerfile` + `docker-compose.yml` + `.env.example`.

## Phase 3: User Story 2 — Spend guard тримає бюджет (P1)

Незалежний тест: cap 10 000, батч 11 000 → відхилено до відправки, у леджері `rejected`.

- [ ] T-007 [FR-001-05, FR-001-04] critical: Інтеграція guard→ledger→pipeline. Тест `tests/test_spend_integration.py` (два батчі, що разом перевищують cap: перший accepted, другий rejected, сумарний леджер ≤ cap). Імпл `python/itb/pipeline.py` (доповнення) — без нових модулів.

## Phase 4: User Story 3 — Суддя перевіряє (P2)

Незалежний тест: фікстура ≥ 10 tx → `verify` exit 0; зіпсована позиція → exit 1 із сигнатурою.

- [ ] T-008 [FR-001-08] critical: Скрипт verify. Тест `tests/test_verify.py` (збіг 100% → 0; одна зіпсована позиція → 1 + сигнатура; `missing` слот не падає). Імпл `scripts/verify.py`. Контракт `contracts/verify.md`.

## Phase 5: Безпека секретів + CI (P1-блокер мержу)

- [ ] T-009 [FR-001-09, FR-001-10] Ключі через volume/env + CI-скан. Тест `tests/test_secrets.py` (репозиторій без `.env`/ключів: `.env.example` без секретів, `.gitignore` покриває `keys/`, `*.key`, `.env`; сканер знаходить підкинутий фейковий keypair у tmp-копії). Імпл `.gitignore` (доповнення) + `.github/workflows/ci.yml` (скан секретів + `trace.py --check` + `pytest`).

## Phase 6: User Story 4 — Локальна розробка (P2)

Незалежний тест: локальний профіль без mainnet — батч зібрано, блок розпарсено.

- [ ] T-010 [FR-001-12] Локальний профіль compose + фікстура блока. Тест `tests/test_local.py` (парсинг фікстури `tests/fixtures/block_<slot>.json` у позиції; compose-профіль `local` не містить mainnet RPC). Імпл `docker-compose.yml` (профіль `local`) + `tests/fixtures/block_*.json` (`trace: ignore-file`) + доку `docs/local-dev.md`.

## Phase 7: Наскрізний dry-run (Definition of Done фічі)

- [ ] T-011 [FR-001-01, FR-001-06, FR-001-07, FR-001-11] E2E dry-run на 6 валідаторах-заглушках. Тест `tests/test_e2e_dryrun.py` (прогін `pipeline.run(dry-run)` → для кожного валідатора вікно або `no-window` з причиною; `sent.csv`/`landed.csv`/`snapshot` містять `config_version`; guard-розрахунок у логах). Імпл без нових файлів — зв'язує T-001..T-006 (дрібні правки `pipeline.py`/`storage.py` за потреби).

## Покриття FR

| FR | Задачі |
|---|---|
| FR-001-01 | T-006, T-011 |
| FR-001-02 | T-006 |
| FR-001-03 | T-001 |
| FR-001-04 | T-002, T-007 |
| FR-001-05 | T-003, T-007 |
| FR-001-06 | T-004, T-011 |
| FR-001-07 | T-005, T-011 |
| FR-001-08 | T-008 |
| FR-001-09 | T-009 |
| FR-001-10 | T-009 |
| FR-001-11 | T-001, T-011 |
| FR-001-12 | T-010 |

## Ескалації

Жодної поки. Маршрут: 2 червоні спроби / `BLOCKED` / 2× `CHANGES_REQUESTED` →
`implementer-senior` + рядок `escalated: T-xxx implementer->implementer-senior, reason=...` нижче.
