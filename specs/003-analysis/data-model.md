# Data Model: 003-analysis

## Pair

`{slot, batch_id, a_sig, b_sig, pos_a, pos_b, key_a, key_b, tie: bool}` —
для гіпотези key ∈ {cu_price, reward_per_cu, send_idx}.

## MetricSet (на validator × arm)

| Поле | Тип |
|---|---|
| `n_pairs`, `n_batches`, `landing_rate` | int, int, float |
| `agreement` | dict hypothesis → float \| None (None при 0 нетієвих пар) |
| `tau`, `ci_low`, `ci_high` | float (по керованій змінній рукава) |
| `p_value` | float (пермутаційний, H0) |
| `gap_median`, `norm_pos_median` | float |
| `verdict` | strict \| statistical \| none \| insufficient-data + `reason` |
