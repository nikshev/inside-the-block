# Implementation Plan: 003-analysis

**Branch**: `003-analysis` | **Date**: 2026-10-23 | **Spec**: `specs/003-analysis/spec.md`

## Summary

Чистий stdlib-модуль `python/itb/analysis.py` (пари, agreement, τ, bootstrap,
пермутації, розриви, вердикти) + `python/itb/report.py` (Markdown/CSV-таблиці).
Вхід — `sent.csv`/`landed.csv`/`blocks/` з 001/002. Жодної мережі.

## Technical Context

**Language**: Python 3.12, stdlib (`random`, `math`, `statistics`).
**Testing**: синтетичні фікстури в тестах; інваріанти SC-001..003.
**Constraints**: O(n²) на слот прийнятний (десятки tx); bootstrap B=1000.

## Constitution Check

- III: `min_pairs`, `bootstrap_samples`, `bootstrap_seed` — у
  `config/experiment.yaml` (секція `analysis`).
- V: кожна цифра звіту — з `data/`; `report.py` друкує джерело кожної таблиці.

## Structure

```text
python/itb/analysis.py   # impl: FR-003-01..05
python/itb/report.py      # impl: FR-003-06
tests/test_analysis.py   # verifies: FR-003-01..05
tests/test_report.py      # verifies: FR-003-06
specs/003-analysis/contracts/analysis.md
```

## Decisions

- **R1. Пари лише всередині одного слота**, міждобові порівняння заборонені.
- **R2. Bootstrap по батчах** (кластерна структура), не по парах.
- **R3. Пермутації всередині слотів** (зберігають载ку слотів).
