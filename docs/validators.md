# Validator Selection and Attribution

## Selection Method

For epoch 1066, candidates were ranked by the number of leader slots in `getLeaderSchedule`, which is proportional to stake and provides more measurement windows. The full `getClusterNodes` snapshot is stored in `data/validators_snapshot.json` (3,909 nodes at collection time).

The table lists seven candidates. Five were targeted for the main measurements; two low-frequency candidates were retained as exploratory options.

| ID | Validator identity | Leader slots / epoch | Version | validators.app name | Jito-enabled |
|---|---|---:|---|---|---|
| V1 | `DRpbCBMxVnDK7maPM5tGv6MvB3v1sRMC86PZ8okm21hy` | 12,136 | 4.3.2 | Binance Staking | Yes |
| V2 | `CAo1dCGYrB6NhHh5xb1cGjUiu86iyCfMTENxgHumSve4` | 9,208 | 4.3.2 | Kraken 2 | Yes |
| V3 | `HEL1USMZKAL2odpNBj2oCjffnFGaYwmbGmyewGv1e2TU` | 15,664 | 4.3.2 | Helius | Yes |
| V4 | `JUPiTERrZqgf1jUyR7dSkhMx4Kn2qJyekWsg3LT1h4b` | 9,660 | 26.10.4 | Jupiter | Yes |
| V5 | `EvnRmnMrd69kFdbLMxWkTn1icZ7DCceRhvmb2SJXqDo4` | 7,796 | 26.10.4 | Everstake | Yes |
| V6 | `GGX3BEoZDqjxcw4AbCdu62ZTMrkpSgmPt81oP2mVuZNS` | 132 | 4.3.0 | HashKey Cloud | Yes |
| V7 | `mds4GEuiSgQRqveGyktWpETBFCb4AS2wDnhqwLHcT6Z` | 340 | 4.4.0-beta.1 | Unidentified | No |

## Attribution Caveats

validators.app marks all five targeted validators as Jito-enabled. The `jito` flag identifies Jito-enabled operation; it does not, by itself, prove the exact client binary or fork. The targeted validators reported version strings 4.3.2 or 26.10.4.

Validators with the same version string showed different ordering behavior: DRpbCBMx had fee-ordered dense batches, while CAo1dCGY and HEL1USMZ did not show a statistically supported fee rule. This points to possible operator configuration or transaction-arrival timing effects; version strings alone do not explain the difference.

The campaign did not establish three distinct client implementations, as originally targeted by the PRD. No high-stake Frankendancer/Firedancer candidate was conclusively identified in the selected sample. This remains an explicit scope limitation; fork identity is not inferred from version strings.
