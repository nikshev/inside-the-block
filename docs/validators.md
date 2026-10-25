# Вибір валідаторів (епоха 1066, 2026-10-24; атрибуція validators.app, 2026-10-24)

Критерій: кількість leader-слотів у `getLeaderSchedule` ∝ стейк → часті вікна.
Версії — як є в `getClusterNodes`. Клієнт — за прапором `jito` validators.app
(jito:true = Jito-Solana/Jito-enabled; jito:false = немодифікований Agave).
Повний знімок: `data/validators_snapshot.json` (3909 нод).

| # | Валідатор | Слотів | Version | jito | Оператор |
|---|---|---|---|---|---|
| V1 | DRpbCBMxVnDK7maPM5tGv6MvB3v1sRMC86PZ8okm21hy | 12136 | 4.3.2 | true | binance staking |
| V2 | CAo1dCGYrB6NhHh5xb1cGjUiu86iyCfMTENxgHumSve4 | 9208 | 4.3.2 | true | Kraken 2 |
| V3 | HEL1USMZKAL2odpNBj2oCjffnFGaYwmbGmyewGv1e2TU | 15664 | 4.3.2 | true | Helius |
| V4 | JUPiTERrZqgf1jUyR7dSkhMx4Kn2qJyekWsg3LT1h4b | 9660 | 26.10.4 | true | Jupiter |
| V5 | EvnRmnMrd69kFdbLMxWkTn1icZ7DCceRhvmb2SJXqDo4 | 7796 | 26.10.4 | true | Everstake |
| V6 | GGX3BEoZDqjxcw4AbCdu62ZTMrkpSgmPt81oP2mVuZNS | 132 | 4.3.0 | true | HashKey Cloud |
| V7 | mds4GEuiSgQRqveGyktWpETBFCb4AS2wDnhqwLHcT6Z | 340 | 4.4.0-beta.1 | false | (без імені; єдиний non-jito кандидат) |

Ключовий факт: **однакові version string містять протилежні поведінки**
(DRpb слідує fee, CAo1/HEL — ні; обидва jito:true). Отже, різниця — не версія
клієнта, а конфігурація оператора або таймінг надходження. Версія ≠ клієнт:
точні білди форків (Frankendancer/Firedancer) за version string не
розрізняються; це обмеження записано чесно, а не замовчано.
