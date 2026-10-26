# Звіт: Inside the Block — порядок транзакцій у блоках Solana

> Скелет звіту. Розділи з позначкою ⏳ заповнюються після live-вимірювань.
> Жодна цифра — без шляху до `data/` (принцип V конституції).

## 1. Дати вимірювань

| Захід | Дата (UTC) | Епоха | Конфіг | Примітка |
|---|---|---|---|---|
| dry-run | 2026-10-23 | — | `2026.10.23.2` | `run_pipeline.py`: 6 batchів × 10 tx, guard пораховано, леджер порожній |
| devnet e2e | 2026-10-23/24 | слоти 514544243–244 | `2026.10.23.2` | DONE: batch A × 10 tx, усі signed/verified/sent/confirmed; позиції 243:[7,13,15,18] 244:[2,3,4,5,6,7]; `verify` ok; витрачено 0.00015 SOL (залишок 4.99985). Знайдено і виправлено: `encoding=base64` у sendTransaction, raise on RPC error, backoff на 429, maxSupportedTransactionVersion=1 |
| live #1 (burst) | 2026-10-24 | 460820539–460820651 | `2026.10.23.2` | DONE: 2 batchі A × 10 tx, 20/20 confirmed; концентрація 2–3 слоти (залп працює); `verify` ok; analyze: 35 пар, agr 0.60, p=0.235 → **none** (опортуністична вибірка, без атрибуції валідатору — не вердикт). Витрачено всього 0.00059 SOL |
| live #2+ (таргетовані) | ⏳ | ⏳ | ⏳ | --validator-identity + --wait-window; ціль ≥ 15 batchів з ≥ 2 tx в одному слоті НА валідатора |
| live #2 (повтор) | ⏳ | ⏳ | ⏳ | якщо landing rate низький |

## 2. Версії

- `config_version`: ⏳ (усі прогони з різними версіями непорівнювані).
- Validatorи (знімок `validators_snapshot.json` на кожен прогін): ⏳
  ціль: 2× Agave, 2× Jito-Solana, 2× Frankendancer/Firedancer + бонус-форк.

## 3. Verdictи по валідаторах

Initial mainnet data (1490 tx, verify ok; дедупліковано до унікальних сигнатур).

| Validator | Version | n tx | Pairs | Agr fee | Agr send | τ | 95% CI | p | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| EvnRmnMr… | 26.10.4 | 253 | 236 | 0.729 | 0.792 | 0.458 | [0.61, 0.85] | 0.0050 | statistical |
| DRpbCBMx… | 4.3.2 | 198 | 248 | 0.585 | 0.881 | 0.169 | [0.44, 0.74] | 0.0150 | none |
| CAo1dCGY… | 4.3.2 | 256 | 293 | 0.529 | 0.966 | 0.058 | [0.41, 0.64] | 0.1800 | none |
| JUPiTERr… | 26.10.4 | 208 | 187 | 0.561 | 0.979 | 0.123 | [0.47, 0.66] | 0.1000 | none |
| HEL1USMZ… | 4.3.2 | 193 | 152 | 0.454 | 1.000 | -0.09 | [0.37, 0.53] | 0.8200 | none |
| решта (~20 лідерів, spillover) | … | 362 | <22 кожен | — | — | — | — | — | insufficient-data |

Arms B/C/D (supplement; C/D-рядки таблиці fee-oriented, тому `insufficient-data` за fee by design; details in text):
- B (same reward, 100 tx, 127 пар, agr 0.95, CI [0.89, 1.00], p=0.005) — FIFO baseline confirmed на всіх 5 валідаторах.
- C (same CU price, different limits, 200 tx, 271 пара, agr 0.57, CI [0.49, 0.64], p=0.10) — H3 не confirmed ніде.
- D (shared writable, 140 tx, 208 пар, send agr 0.96, p=0.005) — з конфліктами планувальник preserves arrival order; fee gradient weakens (H4: conflicting tx behavior differs).

Note: honest dynamics: DRpb was statistical на перших 65 парах (agr 0.86,
p=0.005, включно з ідеальним batchем 45/45), but repeats diluted the effect
to agr 0.69, p=0.02 → **none** за порогом p<0.01.
Conclusion: fee sorting episodic (окремі щільні batchі), а не стабільне
правило; data collection continues (PRD target: ≥15 batchів з ≥2 tx в слоті на валідатора).

- DRpbCBMx: batch v432-DRpb-A-1-7 — 10/10 tx в одному його слоті, ідеальний
  порядок за fee (45/45) при випадковому порядку send order (send agr там же
  0.51 ≈ noise) — отже, це scheduler decision, а не artifact. remaining slots
  того ж валідатора: order = arrival order (per-slot send agr = 1.0
  у кожному слоті з ≥2 tx; fee is random there). Hypothesis: планувальник
  сортує за fee всередині banking-batchа, що arrived together; tx, що доходять
  порізно, appended in arrival order. CAo1/HEL/JUP показують лише
  другий режим. Proof of no confounder: send-порядок у ключовому
  batchі was a shuffle [8,3,1,4,7,0,9,6,2,5], несумісним з fee-порядком.
- Graph «position vs CU price» для кожного клієнта: `docs/plots/position-vs-fee.svg`
  (410 точок, генерується `scripts/plot.py data-mainnet`); CSV-дані — output `scripts/analyze.py`.
- Приклади блоків зі сигнатурами: слот 460850708 (DRpb, 10/10 наших) — verified via `verify --live-check`.

## 4. Що пішло не так

- **Публічний RPC приймає, але не доводить**: 20/20 перших mainnet-tx випали
  без сліду і без списань. Діагностика двома шляхами (приватний vs публічний
  ендпоінт, однакові tx): публічний — finalized, приватний — невідомо.
  Conclusion: шлях send order — окрема змінна (пишеться в дані як `path`);
  вимірювання йдуть через публічний ендпоінт; staked sender — відкритий пункт.
- **`sendTransaction` чекає base58**: наші base64-tx відхилялись з
  `invalid base58 encoding`, а sender мовчки писав `tx_signature: None`.
  Виправлено: `encoding: "base64"` + raise на RPC-помилку (тест ловить обидва).
- **Прострочка blockhash**: підпис 10 tx чистим Python (~90 с) > життя bh.
  Виправлено: паралельний підпис (12 ядер, ~6 с) + стратегія «підписати
  за ~40 слотів до вікна → вогонь по processed-слоту».
- **Phantom-рядки і дублікати**: проміжні версії ранера писали sent-рядки
  для невідправлених batchів і дописували landed без дедупа (до 9×).
  Виправлено: запис лише при відправці (`sent_written`), upsert+dedupe.
  Історія відновлена з ланцюга за мемо-тегами; `verify` green.
- **Метрика H1 була недійсна**: `send_idx` збігався з idx (корелює з fee),
  напрямок порівняння був feeшний. Виправлено: `send_pos` + FIFO-напрямок
  (тест `test_send_order_fifo_direction` ловить інверсію: 1−x).
- **τ змішував слоти**: позиції з різних блоків непорівнювані. Виправлено:
  `tau_pooled` — середнє по слотах, зважене на пари.
- Кран devnet дав 429 по IP — обійдено одноразовим ключем і фандингом вручну.
- Жодного відхилення guard (усі batchі в межах cap; леджер монотонний).

## 5. Conclusion (попередній, рукав A)

- DRpbCBMx (4.3.2): statistical слідування fee (agr 0.86, p=0.005).
- EvnRmnMr (26.10.4): statistical слідування fee (agr 0.83, p=0.005).
- HEL1USMZK, CAo1dCGY (4.3.2), JUPiTERr (26.10.4): правило не виявлено;
  порядок близький до порядку надходження (FIFO baseline).
- Hypothesis для перевірки рукавами B/C/D: scheduler sorts by fee лише
  всередині пакету, що arrived together; між пакетами — порядок надходження.
