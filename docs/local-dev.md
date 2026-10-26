# Local Development (FR-001-12)

Use `solana-test-validator` for local block-parsing tests and devnet for a free end-to-end check. Keep devnet keys separate from mainnet keys; local and devnet activity must not spend the mainnet budget.

## Start a Local Validator

```bash
docker compose --profile local up
```

The `local` profile in `docker-compose.yml` starts `solana-test-validator --reset` on ports 8899 and 8900. It does not start the mainnet pipeline or configure a mainnet RPC endpoint.

## Run the Offline Dry-Run

```bash
python3 scripts/run_pipeline.py
```

The pipeline builds and signs the configured batches, reports the spend-guard estimate, and stops before sending.

## Devnet End-to-End

The devnet runner accepts an explicit RPC URL and keypair file. Use only a devnet-funded keypair:

```bash
python3 scripts/run_devnet.py --live \
  --rpc https://api.devnet.solana.com \
  --keypair keys/devnet-e2e.json \
  --arm A --batches 1 --burst
```

The `keys/` directory is git-ignored. Do not reuse the mainnet keypair for devnet. The fixture `tests/fixtures/block_100.json` documents the stored `getBlock` shape used by `storage.save_block` and `verify.load_block_sigs`.
