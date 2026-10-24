# Вибір валідаторів (епоха 1066, 2026-10-24)

Критерій: кількість leader-слотів у `getLeaderSchedule` ∝ стейк → часті вікна.
Версії — як є в `getClusterNodes` (клієнтська атрибуція — через validators.app,
pending; див. нижче). Повний знімок: `data/validators_snapshot.json` (3909 нод).

| # | Identity | Слоти/епоха | Version | Сім'я (умовно) |
|---|---|---|---|---|
| V1 | DRpbCBMxVnDK7maPM5tGv6MvB3v1sRMC86PZ8okm21hy | 12136 | 4.3.2 | A (домінантна) |
| V2 | CAo1dCGYrB6NhHh5xb1cGjUiu86iyCfMTENxgHumSve4 | 9208 | 4.3.2 | A |
| V3 | HEL1USMZKAL2odpNBj2oCjffnFGaYwmbGmyewGv1e2TU | 15664 | 4.3.2 | A (Helius) |
| V4 | JUPiTERrZqgf1jUyR7dSkhMx4Kn2qJyekWsg3LT1h4b | 9660 | 26.10.4 | B (Jupiter) |
| V5 | EvnRmnMrd69kFdbLMxWkTn1icZ7DCceRhvmb2SJXqDo4 | 7796 | 26.10.4 | B |
| V6 | GGX3BEoZDqjxcw4AbCdu62ZTMrkpSgmPt81oP2mVuZNS | 132 | 4.3.0 | C (рідкісна, бонус) |
| V7 | mds4GEuiSgQRqveGyktWpETBFCb4AS2wDnhqwLHcT6Z | 340 | 4.4.0-beta.1 | D (бета, бонус) |

Вже виміряні лідери (opportunistic, live #1): `CjmXSapt…` (120 слотів, 4.3.2),
`DRpbCBMx…`, `CAo1dCGY…` — усі сім'я A.

## Атрибуція клієнтів — ВІДКРИТЕ ПИТАННЯ

`getClusterNodes` повертає голі номери без назв клієнтів; validators.app API
потребує токен. Гіпотези (не факти): 4.x = Agave; 26.10.x = ?; β-версії = ?.
Розв'язати вручну (6 сторінок validators.app) або контактом лістингу до сабміту.
Вимірювання групуються за version string — це валідно незалежно від назв.
