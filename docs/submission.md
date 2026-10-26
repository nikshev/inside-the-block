# Submission Checklist

Maps the repository deliverables to the Superteam Ukraine bounty PRD.

## Required Deliverables

- [x] Repository with runnable Python 3.12 code.
- [x] One-command default dry-run: `docker compose up`.
- [x] Explicit live mode and spend cap; keypairs are mounted from `./keys`, RPC URLs come from environment variables, secrets are excluded from git and scanned in CI.
- [x] Raw mainnet records committed under `data-mainnet/`: `sent.csv`, `landed.csv`, `blocks/`, `leaders.json`, and the spend ledger; the validator snapshot is at `data/validators_snapshot.json`.
- [x] `scripts/verify.py` checks saved block positions and supports `--live-check` against RPC.
- [x] README explains the design, all six validity risks, and the three factors the experiment cannot isolate.
- [x] `scripts/analyze.py` computes validator/leader and arm metrics and renders report tables.
- [x] Final report at `docs/report.md`, with verdicts, uncertainty, a plot, and a “What Went Wrong” section.
- [x] Position-versus-fee plot at `docs/plots/position-vs-fee.svg`.
- [x] Validator selection and validators.app attribution documented in `docs/validators.md`.

## Mainnet Campaign

- [x] 1,490 unique landed transactions from 149 ten-transaction send attempts; all saved positions pass `verify`.
- [x] Arms A, B, C, and D exercised on mainnet.
- [x] The PRD target of at least 15 qualifying send attempts directed at each validator was met for all five targets: DRpbCBMx 21, EvnRmnMr 26, CAo1dCGY 25, JUPiTERr 22, HEL1USMZ 20. An attempt qualifies when at least two transactions landed in the same slot and the recorded slot leader matched the target. Attempts were counted from contiguous groups of ten sent records, keeping reruns with reused memo batch labels separate.
- [x] Validator-level null results and confidence intervals are included, not only positive findings.
- [x] Graphify/Obsidian vault generated locally from the repository.

## Scope and Data Limitations

- [ ] **Three distinct client implementations were not confirmed.** validators.app marks all five targeted validators as Jito-enabled. Version strings do not identify the exact client or fork binary. See `docs/validators.md` and `docs/report.md`.
- [ ] **Send-timestamp coverage is incomplete.** 1,180 of 1,490 sent records have a recorded timestamp; timestamps for 310 records reconstructed from on-chain memo tags were unavailable and are represented as zero.
- [ ] **Batch-label reuse:** 13 memo `batch_id` labels were reused across reruns. Signatures and slots remain unique and verifiable; this limitation is documented in `docs/report.md`.
- [ ] Exact transaction receipt time at the leader, parallel execution decisions, and operator-specific configuration versus client defaults cannot be isolated with the available data.

## Reproduction Checks

```bash
python3 scripts/verify.py data-mainnet/
python3 scripts/verify.py data-mainnet/ --live-check --rpc "$RPC_URL"
python3 scripts/analyze.py data-mainnet/ --min-pairs 10 --by-leader
python3 scripts/plot.py data-mainnet/ --out docs/plots/position-vs-fee.svg
python3 scripts/trace.py --check
PYTHONPATH=python python3 -m pytest -q
python3 scripts/check_docs.py
```
