# Tasks: 003-analysis

## Phase 1: Метрики

- [x] T-020 [FR-003-01] critical: Пари + agreement за 3 гіпотезами (нічиї виключаються). Тест `tests/test_analysis.py::TestAgreement`. Імпл `python/itb/analysis.py`.
- [x] T-021 [FR-003-02] Kendall τ + bootstrap CI по батчах. Тест `::TestTau` (ідеальний τ=1.0; CI ідеального не містить 0.5). Імпл там само.
- [x] T-022 [FR-003-03] Пермутаційний тест. Тест `::TestPermutation` (ідеальний p≈0; випадковий p велике). Імпл там само.

## Phase 2: Вердикти і звіт

- [x] T-023 [FR-003-04] Розриви і нормовані позиції. Тест `::TestGaps`. Імпл там само.
- [x] T-024 [FR-003-05] critical: Правило рішення (4 класи). Тест `::TestVerdict` (4 фікстури → 4 класи; 5 пар → insufficient). Імпл там само + `analysis:` у `config/experiment.yaml`.
- [x] T-025 [FR-003-06] Markdown/CSV таблиці. Тест `tests/test_report.py`. Імпл `python/itb/report.py`.

## Покриття FR

| FR | Задачі |
|---|---|
| FR-003-01 | T-020 |
| FR-003-02 | T-021 |
| FR-003-03 | T-022 |
| FR-003-04 | T-023 |
| FR-003-05 | T-024 |
| FR-003-06 | T-025 |

## Ескалації

Жодної поки.
