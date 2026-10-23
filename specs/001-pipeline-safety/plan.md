# Implementation Plan: 001-pipeline-safety

**Branch**: `001-pipeline-safety` | **Date**: 2026-10-23 | **Spec**: `specs/001-pipeline-safety/spec.md`

## Summary

Каркас конвеєра, що робить неможливою випадкову витрату коштів і дає судді
шлях перевірки: одна команда (`docker compose up`) → dry-run до guard →
зупинка без відправки; live лише з `MODE=live`; ліміт у версіонованому YAML;
рішення guard + леджер; JSON-логи; фіксована розкладка `data/`; скрипт
`verify`, що перераховує позиції з сирих блоків; CI ловить секрети і червоний
trace. Жодної вимірювальної логіки (рукави A–D, QUIC/TPU, метрики) — це 002/003.

## Technical Context

**Language/Version**: Python 3.12 (stdlib only для 001; жодних solana-залежностей —
реальний клієнт і підписи їдуть у 002)

**Primary Dependencies**: жодних runtime-залежностей у 001; `pyyaml` лише як
опція парсингу YAML — рішення: stdlib-парсер мінімального підмножини YAML
(flat keys + списки валідаторів) або `pyyaml` у Docker-образі; фінально —
`pyyaml` в образі, локально тести без нього через JSON-еквівалент
(див. Рішення R3)

**Storage**: файли: `config/experiment.yaml`, `data/sent.csv`, `data/landed.csv`,
`data/blocks/*.json`, `data/validators_snapshot.json`, `data/spend_ledger.jsonl`

**Testing**: `pytest` (stdlib-сумісні тести; запуск `python -m pytest` або
`python -m unittest`); кожна задача має рівно один тест, що падає без коду

**Target Platform**: Linux (Docker), локально — будь-який Python 3.12

**Project Type**: CLI-пайплайн у Docker Compose (2 сервіси: `pipeline`, `local-validator` профіль)

**Performance Goals**: dry-run ≤ 60 с на 6 валідаторів (без мережі mainnet);
`verify` ≤ 10 с на 100 tx фікстури

**Constraints**: жодної live-відправки без `MODE=live`; жодного секрету в git;
жодного звернення тестів до mainnet (лише фікстури)

**Scale/Scope**: орієнтир PRD ~1600 tx live — каркас не повинен тримати їх у
пам'яті: потоковий запис у `sent.csv`/леджер по батчах

## Constitution Check

- I. Трасування: кожна задача `T-xxx [FR-001-xx]`, кожен файл `impl: FR-001-xx`,
  кожен тест `verifies: FR-001-xx`; `trace.py` зелений на кожному кроці.
- II. Test-First: тест першим, червоний з очікуваної причини; тести без мережі.
- III. Версіонування: `spend_cap_lamports`, `config_version`, CU-параметри —
  лише в `config/experiment.yaml`; прогін пише версію в логи/леджер/data.
- IV. Межі модулів: `config → guard → ledger → pipeline`; RPC/мережа ховається
  за `Sender` (заглушка в 001, реалізація в 002); парсинг блоків — за `BlockStore`.
- V. Відтворюваність: `verify` перераховує позиції з `data/blocks/`; розбіжність —
  non-zero exit.
- VI. Гроші тримає код: guard рахує `batch_max` до відправки; `spent_after ≤ cap`
  інваріант; live-шлях фізично відсутній у dry-run (немає sender-об'єкта).

Гейти: dry-run перед live; spend-cap зупиняє без людини; нестача даних →
«недостатньо даних» (правило для 003, каркас дає лічильник `missing`); секрети —
CI-стоп.

## Project Structure

```text
specs/001-pipeline-safety/
├── spec.md
├── plan.md              # цей файл
├── data-model.md
├── contracts/
│   ├── config.md        # схема config/experiment.yaml
│   ├── guard.md         # функція рішення guard + формула batch_max
│   ├── ledger.md        # схема spend_ledger.jsonl
│   ├── log-record.md    # схема JSON-логу
│   ├── raw-data.md      # розкладка data/
│   └── verify.md        # CLI-інтерфейс verify
└── tasks.md

config/
└── experiment.yaml      # версіонований приклад (cap ~0.05 SOL, 6+ валідаторів-заглушок)

python/itb/
├── __init__.py
├── config.py            # impl: FR-001-03, FR-001-11
├── guard.py             # impl: FR-001-04 (critical)
├── ledger.py            # impl: FR-001-05 (critical)
├── log.py               # impl: FR-001-06
├── storage.py           # impl: FR-001-07
└── pipeline.py          # impl: FR-001-01, FR-001-02

scripts/
└── verify.py            # impl: FR-001-08 (critical, stdlib; поза IMPL_ROOTS — маркер все одно ставимо)

tests/
├── test_config.py       # verifies: FR-001-03
├── test_guard.py        # verifies: FR-001-04
├── test_ledger.py       # verifies: FR-001-05
├── test_log.py          # verifies: FR-001-06
├── test_storage.py      # verifies: FR-001-07
├── test_pipeline.py     # verifies: FR-001-01
├── test_verify.py       # verifies: FR-001-08
├── test_secrets.py      # verifies: FR-001-09
└── test_local.py        # verifies: FR-001-12

Dockerfile
docker-compose.yml        # impl: FR-001-01, FR-001-12 (профілі default + local)
.env.example
.github/workflows/ci.yml # impl: FR-001-10
```

**Structure Decision**: `python/itb/` замість `src/` — щоб `trace.py` бачив
`IMPL_ROOTS=python` і вимагав маркери; `scripts/verify.py` — CLI для судді,
stdlib-only; інтеграційний dry-run — через `docker compose`, локальний профіль —
`solana-test-validator` заглушка/документація в 001, повна реалізація в 002.

## Modules & Interfaces

| Модуль | Робить | Інтерфейс | Залежить від |
|---|---|---|---|
| `config` | завантажує+валідує YAML, віддає `RunConfig` | `load(path) -> RunConfig` (contracts/config.md) | нічого |
| `guard` | чиста функція рішення | `decide(cap, spent, batch_max) -> (accepted, reason)` (contracts/guard.md) | `config` (типи) |
| `ledger` | append-only запис рішень, відновлення `spent` | `append(entry)`, `spent_total()` (contracts/ledger.md) | нічого |
| `log` | JSON-рядок на stdout/файл | `emit(record: LogRecord)` (contracts/log-record.md) | нічого |
| `storage` | пише `sent.csv/landed.csv/blocks/snapshot` | `write_sent()`, `write_landed()`, `save_block()` (contracts/raw-data.md) | `config` |
| `pipeline` | оркеструє dry-run/live, викликає guard→ledger→log→storage, sender відсутній у dry-run | `run(cfg, mode) -> RunReport` | усі вище |
| `verify` | перераховує позиції з `data/` | `verify(data_dir) -> mismatches` exit 0/1 (contracts/verify.md) | `storage` (формати) |

Зовнішні системи (RPC `getBlock`, TPU/QUIC, `solana-test-validator`) за
інтерфейсами `Sender`/`BlockStore` (заглушки в 001, реалізація в 002).

## Key Decisions

- **R1. Python + stdlib для 001.** Швидкість розробки і аналізу важливіша за
  точний таймінг; Rust-сендер — кандидат 002 після вимірювання landing rate.
  Альтернатива (одразу Rust) відхилена: блокер для dry-run/guard/verify, які
  не потребують QUIC.
- **R2. Guard — чиста функція + окремий леджер.** Тест межі (cap, cap+1) без
  файлів; леджер тестується на crash-recovery (перезапуск не дозволяє
  подвійної витрати). Альтернатива (guard пише файл сам) відхилена: змішує
  рішення і стан, ламає принцип IV.
- **R3. YAML з `pyyaml` в образі, тести через dict-еквівалент.** Не тягнемо
  залежність у unit-тести; парсер приймає і dict (тести), і YAML-файл (прод).
- **R4. Підписи в dry-run — детермінована заглушка** `sha256(payload|pubkey)`,
  явно позначена `stub_signature=true`. Реальний ed25519 — у 002. Причина:
  001 доводить каркас і безпеку без solana-залежностей; заглушка не може
  потрапити в live, бо live-шлях ще не існує.
- **R5. `verify` на stdlib, читає лише `data/`.** Суддя запускає без нашого
  оточення: `python3 scripts/verify.py data/`. Live-звірка (`--live-check`)
  — тонкий шар поверх того самого порівняння, реалізація в 002.
- **R6. Compose-профілі: default=dry-run, `MODE=live` + `local`.** Жодного
  окремого прапорця `--send`: режим лише через env, що видно в логах.

## Risks / Open (з PRD, що 001 не закриває)

- Landing rate невідомий → 002 міряє першим dry-run + devnet.
- Alpenglow змінив слоти/вікна → 002 перевіряє таймінг першим ділом.
- RPC для `getBlock`/WS не вибрано → 002 фіксує в конфігу.
- Мова сендера (Rust vs Python) → рішення в 002 за даними landing rate.
- Staked sender третьої сторони → відкрите питання до контакта лістингу.

## Complexity Tracking

Порушень конституції немає. Найскладніше — guard+ledger (critical),
тому вони розбиті на два модулі і два тести замість одного.
