# Contract: analysis

## Функції (`python/itb/analysis.py`, `impl: FR-003-01..05`)

- `pairs_in_slot(landed_rows, key_of) -> list[Pair]` — усі невпорядковані пари
  одного слота; `tie=True` якщо ключі рівні (виключаються з agreement).
- `agreement(pairs) -> float | None` — частка пар, де раніша позиція має
  вищий ключ; безлад = 0.5.
- `kendall_tau(xs, ys) -> float` — класичний τ-a (нічиї в чисельнику 0).
- `bootstrap_ci(batches, stat, B, seed) -> (lo, hi)` — 2.5/97.5 перцентилі.
- `permutation_p(batches, stat, P, seed) -> float` — (1 + #{perm ≥ obs})/(1+P).
- `verdict(m, min_pairs) -> (label, reason)` — правило PRD:
  `n < min_pairs` → insufficient-data; `agr ≥ 0.95 і ci_low > 0.5` → strict;
  `p < 0.01` → statistical; інакше none.
- `gaps(landed_rows, block_sizes) -> (median_gap, median_norm_pos)`.

## Звіт (`python/itb/report.py`, `impl: FR-003-06`)

`render_markdown(results) -> str`, `render_csv(results) -> str` —
таблиця validator × hypothesis з agreement і CI.
