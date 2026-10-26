# Inside the Block — Transaction Ordering in Solana Blocks

An empirical Solana mainnet study of how validators order transactions within blocks, prepared for the Superteam Ukraine “Inside the Block” bounty. The evidence is based on the positions of our own signed transactions in real blocks.

## Research Questions

For each targeted leader:

1. Which observable factor predicts transaction order: priority fee, reward per compute unit, arrival order, account conflicts, or another factor?
2. How consistently does a candidate rule predict pairwise order, with confidence intervals?
3. Is the observed order distinguishable from randomness, or is the justified conclusion “no rule detected” / “insufficient data”?

## Run

```bash
cp .env.example .env
docker compose up                         # safe dry-run by default
MODE=live docker compose up               # live mode; spend guard still applies
```

The dry-run builds and signs transactions, reports the estimated maximum batch cost, and stops before sending. Live sends require an explicit live mode and an accepted spend-guard decision. To target a mainnet leader, use a funded key mounted under `./keys` and provide the RPC endpoint through the environment:

```bash
python3 scripts/run_devnet.py --live \
  --rpc "$RPC_URL" --keypair keys/mainnet.json \
  --validator-identity <VALIDATOR_ID> --label <RUN_LABEL> \
  --arm A --burst --batches 1
```

Despite the script name, `--live --rpc` can use mainnet or devnet; choose the RPC and keypair for the intended cluster. The committed mainnet key is never included in the repository.

## Budget and Key Safety

- The versioned cap is `spend_cap_lamports: 50000000` (0.05 SOL) in `config/experiment.yaml`.
- The guard computes the maximum batch fee before sending and appends decisions to `data-mainnet/spend_ledger.jsonl`.
- Keypairs are mounted from `./keys`; RPC URLs are supplied through environment variables. Neither key material nor `.env` belongs in git.
- CI scans for secrets and checks tests, documentation, and traceability.

## Architecture

```text
config/experiment.yaml       versioned run, arm, budget, and analysis settings
python/itb/                  config, guard, ledger, logging, storage, pipeline
  base58.py / ed25519.py     address encoding and transaction signatures
  txbuilder.py               Solana message serialization (Memo + ComputeBudget)
  arms.py                    experimental arms A–D and seeded send ordering
  schedule.py / sender.py    leader windows and RPC/direct-TPU transport interface
  collector.py / measure.py  block-position collection and batch orchestration
  analysis.py / report.py    pairwise metrics, inference, Markdown/CSV output
scripts/verify.py            compare recorded positions with raw blocks / live RPC
scripts/analyze.py           analyze a data directory by target leader or actual leader
scripts/plot.py              SVG position-versus-CU-price plot
data-mainnet/                raw sent/landed records, blocks, leader map, spend ledger
data/validators_snapshot.json
                             validator snapshot used for candidate attribution
tests/                       offline fixtures and local HTTP stubs; no network tests
```

Runtime code uses Python 3.12 and the standard library. The Ed25519 implementation is checked against an independent implementation; the transaction builder is checked byte-for-byte against the Solana SDK (`solders`).

## Experimental Design

The experimental unit is a batch of 8–12 of our transactions. We target a validator leader window, randomize send order with a recorded seed, and analyze only pairs of our transactions that landed in the same slot.

| Arm | Controlled variable | Held constant / setup | Tests |
|---|---|---|---|
| A — Fee gradient | CU price | CU limit; independent payers | H2 against H0/H1 |
| B — Send order | Randomized send order / interval | Equal reward | H1 (FIFO) |
| C — Reward/cost | CU limit at fixed CU price | Independent payers | H3 against H2 |
| D — Conflicts | Fee levels plus shared writable account | Shared payer and writable account | H4 (account conflicts) |

Leader schedules come from `getLeaderSchedule`; actual slot leaders are checked with `getSlotLeaders`. The delivery path and microsecond send timestamp are recorded. RPC sends use `maxRetries=0` to avoid hidden retries/forwarding.

## Design Validity — Six PRD Risks

| PRD risk | How the experiment addresses it |
|---|---|
| Leader schedule and leader identity | Select scheduled windows, record validator snapshots, and check actual slot leaders; off-target transactions are excluded from target-leader conclusions. |
| Backend-to-node delivery path | Record the transport path (`rpc` or `direct-tpu`) as a variable. The mainnet observations in this report used the public RPC path. |
| Interactions among our transactions | Use separate payers for independent arms; share a payer and writable account only in arm D. |
| Competition from other block transactions | Analyze relative order among our own transactions; other transactions provide block-position and gap context. |
| Send order | Randomize within batches using a recorded seed; arm B isolates FIFO behavior. |
| Noise versus signal | Use pairwise agreement, Kendall’s τ, batch bootstrap confidence intervals, and within-slot permutation tests. Thresholds are versioned in YAML. |

## What This Study Does Not Isolate

1. Exact transaction arrival time at the leader versus scheduler policy. We observe our send time, not the validator’s receipt time.
2. Parallel banking-thread execution. `getBlock` exposes entry order, not internal scheduler decisions.
3. Operator config versus client defaults.

## Mainnet Findings

The committed dataset contains **1,490 unique landed transactions** from **149 ten-transaction send attempts**, across **508 slots**. The five targeted validators each exceeded the PRD threshold of 15 qualifying attempts directed at that validator: DRpbCBMx 21, EvnRmnMr 26, CAo1dCGY 25, JUPiTERr 22, and HEL1USMZ 20. An attempt qualifies when at least two of its transactions landed in the same slot and the recorded slot leader matched the target validator. Thirteen memo batch labels were reused across reruns; attempts were distinguished by their contiguous sent-record groups, and signatures and slots remain unique. This data-lineage limitation is documented in the report.

| Target leader | Version | Same-slot pairs | Fee agreement | Permutation p | Verdict |
|---|---:|---:|---:|---:|---|
| EvnRmnMr… | 26.10.4 | 236 | 0.729 | 0.005 | Statistical fee-ordering signal |
| DRpbCBMx… | 4.3.2 | 248 | 0.585 | 0.015 | No statistically supported fee rule |
| CAo1dCGY… | 4.3.2 | 293 | 0.529 | 0.180 | No fee rule detected |
| JUPiTERr… | 26.10.4 | 187 | 0.561 | 0.100 | No fee rule detected |
| HEL1USMZ… | 4.3.2 | 152 | 0.454 | 0.820 | No fee rule detected |

Across arms, FIFO is strongly supported (B: 180 pairs, agreement 0.967, p=0.005); reward-per-cost did not outperform CU price (C: 302 pairs, agreement 0.540, p=0.115); and arrival order remained strong under the shared-account conflict setup (D: 269 pairs, agreement 0.952, p=0.005).

The evidence suggests conditional behavior: some dense same-slot batches are fee-ordered, while separately arriving transactions tend to retain arrival order. It does not show a universal fee-sorting rule. See [`docs/report.md`](docs/report.md) for validator-level results, caveats, and the failure log.

### Client-Diversity Limitation

validators.app marks all five targeted validators as Jito-enabled. We therefore do not claim that the sample represents three distinct client implementations, as the PRD originally targeted. Version strings alone do not establish the exact client or fork binary. This limitation is documented in [`docs/validators.md`](docs/validators.md).

## Verify and Reproduce

```bash
python3 scripts/verify.py data-mainnet/
python3 scripts/verify.py data-mainnet/ --live-check --rpc "$RPC_URL"
python3 scripts/analyze.py data-mainnet/ --min-pairs 10 --by-leader
python3 scripts/plot.py data-mainnet/ --out docs/plots/position-vs-fee.svg
python3 scripts/trace.py --check
PYTHONPATH=python python3 -m pytest -q
```

Raw signatures, slots, transaction parameters, block responses, leader records, configuration version, and spend-ledger records are committed under `data-mainnet/`; the validator snapshot is at `data/validators_snapshot.json`. The original Ukrainian brief is preserved at [`docs/PRD-inside-the-block.md`](docs/PRD-inside-the-block.md).
