# Contract: ledger

## Файл

`data/spend_ledger.jsonl` — append-only, один JSON-об'єкт на рядок
(схема: див. `data-model.md` → SpendLedgerEntry).

## Функції

`append(entry: SpendLedgerEntry) -> None`,
`spent_total(path) -> int` (сума `batch_max` лише `accepted`-записів),
`load_all(path) -> list` (`python/itb/ledger.py`, `impl: FR-001-05`, `critical:`).

## Правила

- запис лише дописується; жодного перезапису історії;
- `spent_after = spent_before + (batch_max якщо accepted інакше 0)`;
- після перезапису процесу `spent_total()` відновлює той самий залишок
  (тест на crash-recovery: append → перевідкрити → total збігається);
- інваріант усього файла: кожен `spent_after ≤ cap` з конфігу прогону.
