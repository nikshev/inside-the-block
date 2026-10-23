# Локальна розробка (FR-001-12)

Без mainnet-бюджету: парсинг блоків — на `solana-test-validator`,
end-to-end — на devnet з окремими ключами і нульовим mainnet-лімітом.

## Локальний валідатор

```bash
docker compose --profile local up
```

Профіль `local` (див. `docker-compose.yml`) піднімає
`solana-test-validator --reset` на портах 8899/8900. Жодного звернення до
mainnet: у compose немає mainnet-ендпоінтів, `pipeline` у цьому профілі не
стартує.

## Devnet end-to-end (безкоштовно)

```bash
cp .env.example .env          # RPC_URL=wss/json devnet-ендпоінт
MODE=dry-run docker compose up
```

Ключі devnet — лише в `./keys` (volume, gitignore). Guard рахує витрати так
само; mainnet-ліміт у цьому прогоні не чіпається, бо sender devnet-ключі
не перетинаються з mainnet.

## Фікстури

`tests/fixtures/block_100.json` — форма сирого `getBlock`, яку розуміють
`storage.save_block` і `verify.load_block_sigs`. Нові семпли блоків класти
поруч у тій самій формі.
