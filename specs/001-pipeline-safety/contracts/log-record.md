# Contract: log-record

## Формат

Один JSON-об'єкт на рядок, stdout + опційно файл. Поля (див. `data-model.md` →
LogRecord): `ts_us, level, batch_id, slot, leader, validator_version,
sent_at_us, path, target_slot, mode, config_version, msg`.

## Функція

`emit(record: dict) -> None` (`python/itb/log.py`, `impl: FR-001-06`):
дописує `ts_us` (мікросекунди), валідує обов'язкові поля
(`batch_id, mode, config_version, msg`), серіалізує компактним JSON.

## Правила

- час відправки `sent_at_us` — int мікросекунд, а не рядок;
- `path` — одне з `direct-tpu`, `staked-sender`, `stub-local`;
- жодних секретів у логах (тест перевіряє відсутність `private|secret|mnemonic`).
