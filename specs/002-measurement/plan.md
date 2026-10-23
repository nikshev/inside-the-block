# Implementation Plan: 002-measurement

**Branch**: `002-measurement` | **Date**: 2026-10-23 | **Spec**: `specs/002-measurement/spec.md`

## Summary

Реальні підписані Solana-tx (stdlib-only: base58 + ed25519 за RFC 8032 +
серіалізація message/tx), рукави A–D з seed-рандомізацією, leader-вікна з
RPC-абстракцією, sender (реальний `rpc`-шлях через urllib + `direct-tpu`
інтерфейс-заглушка), збір позицій з `getBlock`. Усі мережеві дотики — за
інтерфейсами `RpcClient`/`Sender`; тести — лише фікстури + локальний
HTTP-стаб.

## Technical Context

**Language**: Python 3.12, тільки stdlib (urllib, hashlib, json, http.server у тестах).

**Dependencies**: жодних. ed25519 — вендорена еталонна реалізація
(`python/itb/ed25519.py`, позначено походження), тести — вектори RFC 8032.

**Testing**: pytest; RPC — локальний `http.server`-стаб у тесті; жодних
зовнішніх звернень.

**Constraints**: жодної відправки без guard (перевикористання 001);
dry-run без мережі; `maxRetries=0`, без форвардингу.

## Constitution Check

- III: нові CU-параметри рукавів — у `config/experiment.yaml` (розширення схеми, версія бампається).
- IV: `RpcClient` ховає urllib; `Sender` ховає транспорт; парсинг блоків — `collector` поверх `storage` 001.
- II: RFC-вектори падають без правильної реалізації — природний червоний тест.

## Structure

```text
python/itb/
├── base58.py        # impl: FR-002-03 (вектори)
├── ed25519.py       # impl: FR-002-02 (RFC 8032; trace: НЕ ignore — маркер impl)
├── txbuilder.py     # impl: FR-002-01 (message/tx серіалізація)
├── arms.py          # impl: FR-002-04 (генератори A–D + інваріанти)
├── schedule.py      # impl: FR-002-06 (вікна, snapshot версій)
├── sender.py        # impl: FR-002-07 (RpcSender + DirectTpuStub)
├── collector.py     # impl: FR-002-09 (getBlock → landed)
└── measure.py       # impl: FR-002-05, FR-002-08, FR-002-10 (оркестрація батча)

tests/test_base58.py, test_ed25519.py, test_txbuilder.py, test_arms.py,
      test_schedule.py, test_sender.py (http.server стаб), test_collector.py,
      test_measure.py

specs/002-measurement/contracts/{tx.md, arms.md, sender.md, schedule.md, collector.md}
```

## Decisions

- **R1. Чистий Python ed25519.** Без залежностей; повільний (~мс/підпис —
  прийнятно для ~1600 tx), зате відтворюваний і тестований RFC-векторами.
- **R2. `direct-tpu` у 002 — інтерфейс + стаб**, що повертає `NOT-CONNECTED`
  і пише шлях у дані. Реальний QUIC — після виміру landing rate (ризик PRD).
- **R3. Розширення, не заміна 001**: pipeline/guard/ledger/verify не чіпаємо;
  `measure.run_batch` викликає їх.

## Complexity Tracking — немає порушень.
