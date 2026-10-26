# Local Development (FR-001-12)

Without mainnet budget: block parsing on `solana-test-validator`,
end-to-end on devnet with separate keys and zero mainnet limit.

## Local Validator

Profile `local` (see `docker-compose.yml`) starts
`solana-test-validator --reset` on ports 8899/8900. No
mainnet: compose has no mainnet endpoints, `pipeline` does not
start in this profile.

## Devnet End-to-End (Free)

Devnet keys only in `./keys` (volume, gitignore). Guard counts costs
the same way; mainnet limit untouched since devnet keys
don't overlap with mainnet.

## Fixtures

`tests/fixtures/block_100.json` — raw `getBlock` format understood by
`storage.save_block` and `verify.load_block_sigs`. New block samples go
next to it in the same format.