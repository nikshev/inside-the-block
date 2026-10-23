# Contract: config

## Файл

`config/experiment.yaml` (версіонується) + `.env` (не версіонується) + env.

## Схема YAML

```yaml
config_version: "2026.10.23.1"      # обов'язково
spend_cap_lamports: 50000000        # ~0.05 SOL; 0 = заборонити будь-який live
base_fee_lamports: 5000
batch:
  tx_per_batch: 10                 # 8..12
  cu_limit: 200000
  cu_price_lamports: 0
validators:
  - identity: "TestValidator1111111111111111111111111111111111"
    label: "agave-1"
    expected_client: "agave"
rpc:
  http_url_ref: "env:RPC_URL"
  ws_url_ref: "env:WS_URL"
```

## Функція

`load(path_or_dict) -> RunConfig` (`python/itb/config.py`, `impl: FR-001-03`):

- приймає шлях до YAML або dict (тести йдуть через dict, без `pyyaml`);
- валідує: `config_version` присутня, `spend_cap_lamports >= 0`,
  `tx_per_batch` у `8..12`, ≥ 1 валідатор, жодного URL/ключа всередині
  (значення з `env:` — лише посилання);
- кидає `ConfigError` з полем, що порушено; пайплайн не стартує.

## `.env.example`

```
MODE=dry-run
RPC_URL=
WS_URL=
# Жодних приватних ключів. Keypair-и лише через volume ./keys (див. contracts CI).
```
