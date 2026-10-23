# Data Model: 002-measurement (доповнення до 001)

## SignedTx

| Поле | Тип |
|---|---|
| `payload_bytes` | bytes — серіалізоване повідомлення Solana |
| `signature` | 64 bytes ed25519 |
| `signature_b58` | base58 |
| `signer_pubkey_b58` | base58 |
| `memo_tag`, `cu_limit`, `cu_price_lamports`, `payer` | як у 001 |
| `writable_accounts` | list[string] — для рукава D спільний акаунт |

## ArmBatch

`arm: A|B|C|D`, `seed: int`, `levels: list` (рівні дослідної змінної),
`txs: list[SignedTx]`, `send_order: list[int]` (перестановка за seed).

## LeaderWindow

`validator_identity, label, expected_client, epoch, start_slot, end_slot,
actual_leader, version, off_target: bool`.

## SendRecord

`signature_b58, sent_at_us, path: direct-tpu|rpc|stub-local,
target_slot, batch_id, idx`.

Зв'язки: `ArmBatch 1──* SignedTx`; `LeaderWindow 1──* ArmBatch`;
`SignedTx 1──1 SendRecord`.
