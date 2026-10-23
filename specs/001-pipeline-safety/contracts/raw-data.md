# Contract: raw-data

## Розкладка `data/` (FR-001-07)

```
data/
├── sent.csv                  # усі параметри tx і час відправки
├── landed.csv                # signature→slot→position (+missing)
├── blocks/
│   └── <slot>.json           # сира відповідь getBlock (у 001 — фікстура тієї самої форми)
├── validators_snapshot.json  # version string на момент вимірювання
└── spend_ledger.jsonl         # див. contracts/ledger.md
```

## `sent.csv` (заголовок, порядок колонок фіксований)

```
batch_id,idx,signature,memo_tag,validator_label,cu_limit,cu_price_lamports,payer,sent_at_us,path,target_slot,config_version,stub_signature
```

## `landed.csv`

```
signature,slot,position,batch_id,idx,status
```

`status`: `landed` або `missing` (слот пропущено / `getBlock` → null).
Кожна `signature` з `sent.csv` має рівно один рядок у `landed.csv` після
завершення батча.

## `blocks/<slot>.json`

Сирий `getBlock` (jsonParsed або binary — фіксується в полі
`encoding` поруч). Мінімум для `verify`: масив `transactions` зі
`signature` у порядку entries.

## Функції

`write_sent()`, `write_landed()`, `save_block()`, `save_snapshot()`
(`python/itb/storage.py`, `impl: FR-001-07`). Усі — потокові (append),
жодного тримання 1600 tx у пам'яті.
