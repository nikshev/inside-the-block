# Validator Selection (epoch 1066, 2026-10-24; attribution via validators.app, 2026-10-24)

Criterion: leader slots in `getLeaderSchedule` ∝ stake → window share.
Versions as in `getClusterNodes`. Client per `jito` flag in validators.app
(jito:true = Jito-Solana/Jito-enabled; jito:false = unmodified Agave).
Full snapshot: `data/validators_snapshot.json` (3909 нод).

| # | Валідатор | Слотів | Version | jito | Оператор |
|---|---|---|---|---|---|
| V1 | DRpbCBMxVnDK7maPM5tGv6MvB3v1sRMC86PZ8okm21hy | 12136 | 4.3.2 | true | binance staking |
| V2 | CAo1dCGYrB6NhHh5xb1cGjUiu86iyCfMTENxgHumSve4 | 9208 | 4.3.2 | true | Kraken 2 |
| V3 | HEL1USMZKAL2odpNBj2oCjffnFGaYwmbGmyewGv1e2TU | 15664 | 4.3.2 | true | Helius |
| V4 | JUPiTERrZqgf1jUyR7dSkhMx4Kn2qJyekWsg3LT1h4b | 9660 | 26.10.4 | true | Jupiter |
| V5 | EvnRmnMrd69kFdbLMxWkTn1icZ7DCceRhvmb2SJXqDo4 | 7796 | 26.10.4 | true | Everstake |
| V6 | GGX3BEoZDqjxcw4AbCdu62ZTMrkpSgmPt81oP2mVuZNS | 132 | 4.3.0 | true | HashKey Cloud |
| V7 | mds4GEuiSgQRqveGyktWpETBFCb4AS2wDnhqwLHcT6Z | 340 | 4.4.0-beta.1 | false | (без імені; єдиний non-jito кандидат) |

Key fact: **identical version strings exhibit opposite behaviors**
(DRpb follows fee, CAo1/HEL do not; both jito:true). Отже, різниця — не версія
клієнта, а конфігурація оператора або таймінг надходження. Version ≠ client:
exact fork builds (Frankendancer/Firedancer) are not distinguishable by version string;
this limitation is documented honestly, not by default.
