# Contract: verify

## CLI

```
python3 scripts/verify.py data/ [--live-check]
```

- без прапорця: лише локальне порівняння `landed.csv` проти `data/blocks/*.json`
  (суддя без RPC; тести без мережі);
- з `--live-check`: ті самі перевірки + перезапит `getBlock` з RPC
  (реалізація live-шару в 002; у 001 прапорець повертає `NOT-IMPLEMENTED`, exit 2).

## Семантика (`scripts/verify.py`, `impl: FR-001-08`, `critical:`)

1. Для кожної `landed`-запису зі статусом `landed` знайти слот-файл і
   перевірити, що сигнатура на заявленій `position`.
2. Для `missing` перевірити, що слот-файл відсутній або не містить сигнатури.
3. Вивести таблицю `signature → slot → position → OK/MISMATCH`.
4. Будь-який MISMATCH → exit 1 із сигнатурою; усе збіглося → exit 0.

Тест `tests/test_verify.py` (`verifies: FR-001-08`): фікстура з ≥ 10 tx,
100% збіг → exit 0; навмисно зіпсована позиція → exit 1 із сигнатурою.
