# Analysis Digest

**date_dir:** `data/2025-10-02`  
**generated_utc:** 2025-10-02T23:49:24Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-02/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-02/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-02/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-02/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 74.96 | True | 169.1818 | 169.73 | Above | 147.7735 | 2.84 | HOLD |
| ASTS | 83.93 | True | 63.3648 | 66.16 | Above | 43.534 | 2.79 | HOLD |
| BBAI | 70.97 | True | 7.181 | 7.27 | Above | 5.6434 | 2.01 | HOLD |
| META | 37.52 | False | 723.3498 | 727.05 | Above | 720.4221 | 0.73 | HOLD |
| MSFT | 55.49 | True | 515.8348 | 515.74 | Below | 496.2535 | -0.4 | HOLD |
| MSTR | 57.24 | True | 349.4748 | 352.33 | Above | 375.7122 | 3.0 | HOLD |
| MSTU | 55.38 | True | 5.4347 | 5.52 | Above | 7.2668 | 6.07 | HOLD |
| NVDA | 64.04 | True | 189.3961 | 188.89 | Below | 163.1476 | 1.26 | HOLD |
| PLTR | 70.61 | True | 185.8242 | 187.05 | Above | 152.0897 | 0.95 | HOLD |
| QQQ | 73.98 | True | 604.9155 | 605.73 | Above | 557.6755 | 0.63 | HOLD |
| RDDT | 24.6 | False | 202.1512 | 200.92 | Below | 175.3476 | 2.1 | HOLD |
| RKLB | 48.44 | False | 51.0355 | 52.47 | Above | 39.4978 | 1.4 | HOLD |
| UUUU | 75.66 | True | 16.2601 | 16.82 | Above | 8.9 | 1.85 | HOLD |
| VST | 43.98 | False | 202.1831 | 202.65 | Above | 188.4345 | 1.26 | HOLD |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 27.05 | 109.13 | 1 | -8208.0 | -75.21 |  | intrinsic | error | ok | 727.05 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.52 | 1.86 | 20 | -2680.0 | -72.04 |  | intrinsic | error | ok | 5.52 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
_No data_

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
