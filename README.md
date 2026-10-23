# Inside the Block — порядок транзакцій у блоках Solana

Експеримент на mainnet: за яким правилом валідатори різних клієнтів
впорядковують транзакції в блоці (Superteam Ukraine bounty, ~2 500 USDC).
Докази — позиції **наших власних** транзакцій у реальних блоках.

## Ключове питання (на кожен валідатор)

1. Яке правило ставить tx раніше/пізніше (fee, reward/CU, час, блокування)?
2. Наскільки строго (частка пар + довірчий інтервал)?
3. Чи є правило взагалі (або це шум — з обґрунтуванням)?

## Запуск однією командою

```bash
cp .env.example .env        # RPC_URL=..., WS_URL=...
docker compose up           # dry-run за замовчуванням: tx будуються і
                            # підписуються, але НЕ відправляються
MODE=live docker compose up # реальна відправка (після успішного dry-run)
```

Dry-run зупиняється на spend guard і показує розрахунок витрат.
Жодного lamport без `MODE=live` — це властивість конструкції, а не домовленість.

## Бюджет і ключі

- Ліміт — `spend_cap_lamports` у `config/experiment.yaml` (~0.05 SOL).
  Guard рахує максимальну комісію батча **до** відправки, веде
  `data/spend_ledger.jsonl`, досяг ліміту → зупинка.
- Keypair-и лише через `./keys` (volume, gitignore). RPC URL лише через env.
  `.env.example` без секретів; CI ловить секрети (`private key`, мнемоніки,
  base58-довжини) і червоний `trace.py`.

## Архітектура

```
config/experiment.yaml   версіонований конфіг (cap, рукави, пороги аналізу)
python/itb/              config→guard→ledger→log→storage→pipeline (001)
  base58/ed25519/txbuilder/arms/schedule/sender/collector/measure (002)
  analysis/report (003)
scripts/verify.py        landed.csv vs blocks/ (+ --live-check з RPC)
scripts/analyze.py       data/ → метрики → Markdown/CSV
data/                    sent.csv, landed.csv, blocks/, validators_snapshot.json
tests/                   без мережі (фікстури + локальні HTTP-стаби)
```

Мова: Python 3.12, тільки stdlib (ed25519 і base58 — вендорені/власні,
звірені з незалежними реалізаціями: cryptography, solders).

## Дизайн експерименту

Одиниця — **батч**: 8–12 наших tx в одне leader-вікно одного валідатора.
Одна керована змінна, решта рандомізована. До аналізу — лише пари наших tx
в **одному слоті**.

| Рукав | Змінюємо | Фіксуємо | Гіпотеза |
|---|---|---|---|
| A | CU price (10 рівнів) | CU limit, незалежні платники | H2 проти H0/H1 |
| B | порядок/інтервал відправки | однакова винагорода | H1 (FIFO) |
| C | CU limit при однаковому price | незалежні платники | H3 проти H2 |
| D | як A + спільний writable-акаунт | — | H4 (блокування) |

Доставка: розклад `getLeaderSchedule`, відправка за ~1 слот до вікна,
`maxRetries=0`, шлях (`direct-tpu`/`rpc`) пишеться як змінна, час — у
мікросекундах. Валідатори: ≥ 6, ≥ 3 клієнти (Agave, Jito-Solana, Frankendancer+).

## Design Validity — як закрито 6 пунктів

| Пункт PRD | Ризик | Як закриваємо |
|---|---|---|
| Leader schedule і типи лідерів | чужий лідер, зміна клієнта | `schedule.windows` + `getSlotLeaders`-звірка; `off-target` батчі виключаються з аналізу; snapshot версій на прогін |
| Шлях від бекенду до ноди | форвардинг/SWQoS перемішують порядок | шлях — змінна (`direct-tpu`/`rpc`); одне з'єднання; див. невідокремлене №1 |
| Взаємодія наших tx | спільний fee payer = конфлікт | пул платників для незалежних; спільний writable лише в D |
| Конкуренція в блоці | чужі tx витісняють наші | аналізуємо відносний порядок наших; чужі — контекст (заповненість, медіана fee, розриви) |
| Порядок відправки | плутає FIFO і priority | seed-перестановка в кожному батчі, seed у лозі; окремий рукав B |
| Шум проти правила | малі вибірки брешуть | пермутаційний тест + Kendall τ з bootstrap CI; поріг `min_pairs` у YAML |

## Що ми НЕ відокремлюємо (чесно)

1. **час надходження tx до лідера** проти правила планувальника — бачимо лише час відправки;
2. **паралельне виконання** в кількох потоках — порядок у `getBlock` це порядок entries, не рішення планувальника;
3. **налаштування оператора** проти дефолтів його клієнта.

## Перевірка суддею

```bash
python3 scripts/verify.py data/                        # локально
python3 scripts/verify.py data/ --live-check --rpc URL # проти ланцюга
python3 scripts/analyze.py data/ --min-pairs 30        # метрики → таблиця
python3 scripts/trace.py && PYTHONPATH=python python3 -m pytest -q
```

## Витрати (орієнтир PRD)

~20 батчів × 10 tx × 8 валідаторів ≈ 1 600 tx; база 5 000 lamports ≈ 0.008 SOL,
решта — priority fees і повтори. Точні числа — після dry-run.

## Статус

- [x] 001 каркас: конфіг, guard, леджер, dry-run, verify, CI
- [x] 002 вимірювання: реальні підписані tx, рукави, sender, збір
- [x] 003 аналіз: agreement, τ+CI, пермутації, вердикти
- [x] 004 сабміт: цей README, `analyze`, live-check, скелет звіту
- [ ] Live-прогони на mainnet (дати — у `docs/report.md` після виходу на live)
- [ ] Фінальний звіт з вердиктами по валідаторах
