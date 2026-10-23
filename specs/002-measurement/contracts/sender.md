# Contract: sender + schedule + collector

## Sender (`python/itb/sender.py`, `impl: FR-002-07`)

`send(signed_txs, path) -> list[SendRecord]`; `sent_at_us` per-tx до виклику
транспорту.

- `RpcSender(rpc_url)`: `sendTransaction(base64(tx), {"skipPreflight": true, "maxRetries": 0})`
  через urllib; `SendRecord.path="rpc"`.
- `DirectTpuStub`: повертає записи з `path="direct-tpu"`, `note="NOT-CONNECTED"`,
  відправки не робить (реальний QUIC — після виміру landing rate).

## Schedule (`python/itb/schedule.py`, `impl: FR-002-06`)

`windows(schedule_json, validator) -> list[LeaderWindow]`;
`snapshot(nodes_json) -> dict` у формат `validators_snapshot.json`.
Тести — на записаних фікстурах `getLeaderSchedule`/`getClusterNodes`.

## Collector (`python/itb/collector.py`, `impl: FR-002-09`)

`collect(data_dir, rpc_getblock) -> landed.csv`: порядок сигнатур за entries;
відсутній блок → `missing`. Тест — фікстура 3 слотів / 15 tx.
