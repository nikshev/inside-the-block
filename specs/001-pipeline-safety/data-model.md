# Data Model: 001-pipeline-safety

Джерело: `spec.md` (Key Entities). Усі константи, що впливають на результат,
живуть у `config/experiment.yaml` (принцип III); тут — форми даних.

## RunConfig (з `config/experiment.yaml`)

| Поле | Тип | Правило |
|---|---|---|
| `config_version` | string, `YYYY.MM.DD.N` або semver | обов'язкове; пишеться в логи, леджер, `data/`; прогони з різними версіями непорівнювані |
| `spend_cap_lamports` | int > 0 | ~0.05 SOL ≈ 50 000 000; `0` означає «будь-який live відхилити» |
| `base_fee_lamports` | int, default 5000 | базова комісія на tx |
| `mode` | `dry-run` \| `live` | з env `MODE`, default `dry-run`; у 001 live-шлях лише планується |
| `validators` | list[ValidatorRef] ≥ 1 (ціль ≥ 6 у проді) | кожен: `identity, label, expected_client` |
| `batch` | `{tx_per_batch: 8..12, cu_limit, cu_price_lamports}` | CU-параметри батча-заглушки 001 |
| `rpc` | `{http_url_ref: "env:RPC_URL", ws_url_ref: "env:WS_URL"}` | жодного URL у YAML, лише посилання на env |

Інваріант: невідома версія конфігу або відсутній `spend_cap_lamports` →
`load()` падає з поясненням, пайплайн не стартує.

## ValidatorRef

| Поле | Тип |
|---|---|
| `identity` | base58 pubkey (у 001 може бути заглушка `TestValidator111...`) |
| `label` | string (`agave-1`, `jito-1`, ...) |
| `expected_client` | string (`agave`, `jito-solana`, `frankendancer`, ...) |

Знімок фактичної версії (`getClusterNodes` + validators.app) пишеться в
`data/validators_snapshot.json` під час прогону (див. contracts/raw-data.md).

## Batch (одиниця експерименту, у 001 — заглушка)

| Поле | Тип |
|---|---|
| `batch_id` | `YYYYMMDD-HHMMSS-<validator-label>-<seq>`; ідемпотентний ключ |
| `validator` | ValidatorRef |
| `target_window` | `{epoch, start_slot, end_slot}` або `{reason: "no-window"}` |
| `txs` | list[TxCandidate], len = `tx_per_batch` |
| `send_seed` | int; seed рандомної перестановки порядку відправки |

## TxCandidate (001: структура + stub-підпис)

| Поле | Тип |
|---|---|
| `idx` | 0..N-1 |
| `memo_tag` | `"batch_id:idx"` |
| `cu_limit`, `cu_price_lamports` | int |
| `payer` | string (у 001 — мітка `payer-pool-i` або `shared-conflict`) |
| `payload_bytes` | bytes (канонічне кодування полів вище) |
| `signature` | hex `sha256(payload|payer)`; поле `stub_signature: true` |

Реальний ed25519-підпис і Memo+ComputeBudget-інструкції — у 002.

## SpendLedgerEntry (append-only JSONL)

| Поле | Тип |
|---|---|
| `batch_id` | string |
| `decided_at` | ISO8601 UTC |
| `config_version` | string (з RunConfig) |
| `batch_max_lamports` | int = `len(txs)*base_fee + sum(priority_fees)` |
| `spent_before`, `spent_after` | int |
| `decision` | `accepted` \| `rejected` |
| `reason` | `ok` \| `exceeds-cap` \| `cap-zero` \| `no-window` ... |

Інваріант: для всіх префіксів леджера `spent_after ≤ spend_cap_lamports`.

## LogRecord (JSON-рядок)

| Поле | Тип |
|---|---|
| `ts_us` | int, мікросекунди epoch |
| `level` | `INFO` \| `WARN` \| `ERROR` |
| `batch_id`, `slot`, `leader`, `validator_version` | string/int |
| `sent_at_us`, `path`, `target_slot` | int/string |
| `mode`, `config_version` | string |
| `msg` | string |

## LandedRecord (`data/landed.csv`)

`signature, slot, position, batch_id, idx` + окремий статус `missing` для
пропущених слотів (`getBlock` → null). Позиція — індекс нашої tx серед усіх
tx слота за порядком entries.

## ValidatorsSnapshot (`data/validators_snapshot.json`)

`{measured_at, source: "getClusterNodes+validators.app", validators: [{identity, label, version, stake}]}`.
У 001 пишеться заглушка з `source: "stub"` і явною міткою, прод-збір — у 002.

## Зв'язки

```
RunConfig 1──* Batch (через validator + batch-параметри)
Batch 1──* TxCandidate
Batch 1──1 SpendLedgerEntry (рішення guard)
Batch 1──* LogRecord
TxCandidate 1──0/1 LandedRecord (через signature; missing окремо)
RunConfig 1──1 ValidatorsSnapshot (на прогін)
```
