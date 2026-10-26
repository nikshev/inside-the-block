# Inside the Block — Transaction Ordering in Solana Blocks

Mainnet experiment: what rule do validators of different clients
use to order transactions in blocks (Superteam Ukraine bounty, ~2,500 USDC).
Докази — позиції **наших власних** транзакцій у реальних блоках.

## Key Question (per validator)

1. What rule puts tx earlier/later (fee, reward/CU, time, conflicts)?
2. How strict (pair fraction + confidence interval)?
3. Is there a rule at all (or is it noise — with justification)?

## Single-Command Launch

```bash
cp .env.example .env        # RPC_URL=..., WS_URL=...
docker compose up           # dry-run за замовчуванням: tx будуються і
                            # підписуються, але НЕ відправляються
MODE=live docker compose up # реальна відправка (після успішного dry-run)
```

Dry-run stops at spend guard and shows cost estimate.
No lamport without `MODE=live` — this is a design property, not a convention.

## Budget & Keys

- Limit — `spend_cap_lamports` in `config/experiment.yaml` (~0.05 SOL).
  Guard calculates max batch fee **before** send, maintains
  `data/spend_ledger.jsonl`, limit reached → stop.
- Keypairs only via `./keys` (volume, gitignore). RPC URL only via env.
  `.env.example` без секретів; CI ловить секрети (`private key`, мнемоніки,
  base58 lengths) and red `trace.py`.

## Architecture

```
config/experiment.yaml   versioned config (cap, arms, analysis thresholds)
python/itb/              config→guard→ledger→log→storage→pipeline (001)
  base58/ed25519/txbuilder/arms/schedule/sender/collector/measure (002)
  analysis/report (003)
scripts/verify.py        landed.csv vs blocks/ (+ --live-check via RPC)
scripts/analyze.py       data/ → metrics → Markdown/CSV
data/                    sent.csv, landed.csv, blocks/, validators_snapshot.json
tests/                   no network (fixtures + local HTTP stubs)
```

Language: Python 3.12, stdlib only (ed25519 & base58 vendored/own,
verified against independent implementations: cryptography, solders).

## Experiment Design

Unit is **batch**: 8–12 our txs in one leader window of one validator.
One controlled variable, rest randomized. For analysis — only pairs of our txs
in **one slot**.

| Arm | Varies | Fixed | Hypothesis |
|---|---|---|---|
| A | CU price (10 levels) | CU limit, independent payers | H2 vs H0/H1 |
| B | send order/interval | same reward | H1 (FIFO) |
| C | CU limit at same price | independent payers | H3 vs H2 |
| D | like A + shared writable account | — | H4 (conflicts) |

Delivery: `getLeaderSchedule` schedule, send ~1 slot before window,
`maxRetries=0`, path (`direct-tpu`/`rpc`) logged as variable, time in
microseconds. Validators: ≥ 6, ≥ 3 clients (Agave, Jito-Solana, Frankendancer+).

## Design Validity — How 6 Points Are Covered

| PRD Point | Risk | How Covered |
|---|---|---|
| Leader schedule & leader types | wrong leader, client change | `schedule.windows` + `getSlotLeaders` cross-check; `off-target` batches excluded; version snapshot per run |
| Backend-to-node path | forwarding/SWQoS reorder | path is a variable (`direct-tpu`/`rpc`); single connection; see undiff. #1 |
| Our tx interaction | shared fee payer = conflict | payer pool for independent; shared writable only in D |
| Block competition | foreign tx displace ours | we analyze relative order of ours; foreign = context (fill, median fee, gaps) | |
| Send order | confuses FIFO & priority | per-batch seed shuffle, seed in logs; separate arm B | |
| Noise vs rule | small samples mislead | permutation test + Kendall τ + bootstrap CI; `min_pairs` threshold in YAML | |

## What We Do NOT Isolate (Honestly)

1. **tx arrival time at leader** vs scheduler rule — we only see send time;
2. **parallel execution** in multiple threads — `getBlock` order is entries order, not scheduler decision;
3. **operator config** vs client defaults.

## Judge Verification

```bash
python3 scripts/verify.py data/                        # locally
python3 scripts/verify.py data/ --live-check --rpc URL # vs chain
python3 scripts/analyze.py data/ --min-pairs 30        # metrics → table
python3 scripts/trace.py && PYTHONPATH=python python3 -m pytest -q
```

## Costs (PRD Estimate)

~20 batches × 10 tx × 8 validators ≈ 1,600 tx; base 5,000 lamports ≈ 0.008 SOL,
rest — priority fees & retries. Exact numbers after dry-run.

## Status

- [x] 001 scaffold: config, guard, ledger, dry-run, verify, CI
- [x] 002 measurement: real signed txs, arms, sender, collection
- [x] 003 analysis: agreement, τ+CI, permutations, verdicts
- [x] 004 submission: this README, `analyze`, live-check, report skeleton
- [ ] Live runs on mainnet (dates in `docs/report.md` after going live)
- [ ] Final report with per-validator verdicts
