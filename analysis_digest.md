# Analysis Digest

**date_dir:** `data/2025-10-03`  
**generated_utc:** 2025-10-03T18:57:26Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-03/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-03/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-03/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-03/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 54.31 | True | 167.9553 | 163.37 | Below | 148.3264 | 0.56 | TRIM |
| ASTS | 83.44 | True | 67.1992 | 67.12 | Below | 43.9346 | -0.76 | TRIM |
| BBAI | 66.67 | True | 7.191 | 6.95 | Below | 5.6803 | 0.83 | TRIM |
| META | 28.3 | False | 718.4791 | 712.95 | Below | 721.1562 | 0.35 | EXIT |
| MSFT | 52.17 | True | 518.5786 | 517.5865 | Below | 496.936 | 0.26 | TRIM |
| MSTR | 56.37 | True | 352.0091 | 346.425 | Below | 375.1276 | -0.42 | TRIM |
| MSTU | 54.38 | True | 5.5076 | 5.33 | Below | 7.2273 | -0.72 | TRIM |
| NVDA | 59.0 | True | 188.5739 | 185.435 | Below | 163.7721 | 0.16 | TRIM |
| PLTR | 50.34 | False | 178.568 | 171.4 | Below | 152.6208 | -0.35 | TRIM |
| QQQ | 62.5 | True | 605.4802 | 601.45 | Below | 558.6114 | 0.13 | TRIM |
| RDDT | 21.7 | False | 209.1055 | 206.4258 | Below | 176.2993 | 5.52 | EXIT |
| RKLB | 50.01 | True | 53.8764 | 53.9878 | Above | 39.8257 | -0.8 | HOLD |
| UUUU | 66.18 | False | 17.0553 | 16.425 | Below | 9.0176 | 1.43 | TRIM |
| VST | 39.4 | False | 206.0522 | 201.72 | Below | 188.9907 | 0.84 | EXIT |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 12.93 | 109.13 | 1 | -9619.5 | -88.15 |  | intrinsic | error | ok | 712.93 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.36 | 1.86 | 20 | -3000.0 | -80.65 |  | intrinsic | error | ok | 5.36 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
_No data_

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
