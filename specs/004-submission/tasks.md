# Tasks: 004-submission

- [x] T-026 [FR-004-02] analyze CLI: data/ → метрики → таблиці. Тест `tests/test_analyze.py` (синтетичний data/ → strict для ідеального рукава). Імпл `scripts/analyze.py`.
- [x] T-027 [FR-004-03] verify --live-check через RPC. Тест `tests/test_verify_live.py` (локальний стаб: збіг → 0; розбіжність → 1). Імпл `scripts/verify.py` (доповнення).
- [x] T-028 [FR-004-01] README з design validity і невідокремленим. Тест `tests/test_docs.py` (всі 6 пунктів + 3 невідокремлених + команди). Імпл `README.md`.
- [x] T-029 [FR-004-04] Скелет звіту. Тест у `tests/test_docs.py` (розділи: дати, версії, вердикти, графіки, what-went-wrong). Імпл `docs/report.md`.
- [x] T-030 [FR-004-05] Чекліст сабміту. Тест у `tests/test_docs.py` (8 deliverables). Імпл `docs/submission.md`.

- [x] T-031 [FR-001-12] Devnet-ранер однією командою.
- [x] T-032 [FR-004-04] Графік position-vs-fee (SVG, stdlib). Тест `tests/test_plot.py` (5 точок, осі підписані). Імпл `scripts/plot.py` → `docs/plots/position-vs-fee.svg`. Тест `tests/test_run_devnet.py` (dry-run без мережі пише sent.csv; --help показує --rpc/--keypair). Імпл `scripts/run_devnet.py`.

## Покриття FR

| FR | Задачі |
|---|---|
| FR-004-01 | T-028 |
| FR-004-02 | T-026 |
| FR-004-03 | T-027 |
| FR-004-04 | T-029 |
| FR-004-05 | T-030 |

## Ескалації

Жодної поки.
