# Analysis Digest

**date_dir:** `data/2025-09-26`  
**generated_utc:** 2025-09-26T22:59:21Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-26/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-26/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-26/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-26/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 64.91 | True |  | 159.46 | Unknown | 145.2398 | -0.47 | HOLD |
| ASTS | 64.58 | True |  | 49.09 | Unknown | 42.3379 | 1.66 | HOLD |
| BBAI | 69.96 | True |  | 6.73 | Unknown | 5.4966 | 0.28 | HOLD |
| META | 46.15 | False |  | 743.75 | Unknown | 714.9466 | 0.15 | HOLD |
| MSFT | 62.59 | True |  | 511.46 | Unknown | 493.0091 | 0.6 | HOLD |
| MSTR | 39.77 | False |  | 309.06 | Unknown | 378.4034 | 0.2 | HOLD |
| MSTU | 37.18 | False |  | 4.31 | Unknown | 7.4339 | -0.12 | HOLD |
| NVDA | 62.82 | True |  | 178.19 | Unknown | 160.3482 | 0.27 | HOLD |
| PLTR | 72.13 | True |  | 177.57 | Unknown | 149.3148 | -0.04 | HOLD |
| QQQ | 72.62 | True |  | 595.97 | Unknown | 553.0044 | 0.14 | HOLD |
| RDDT | 55.12 | False |  | 240.11 | Unknown | 170.9108 | 0.57 | HOLD |
| RKLB | 47.58 | False |  | 46.26 | Unknown | 38.4269 | 1.44 | HOLD |
| UUUU | 76.63 | True |  | 16.71 | Unknown | 8.4448 | 1.45 | HOLD |
| VST | 63.24 | False |  | 207.22 | Unknown | 186.0639 | -0.21 | HOLD |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 43.75 | 109.13 | 1 | -6538.0 | -59.91 |  | intrinsic | error | ok | 743.75 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.0 | 1.86 | 20 | -3720.0 | -100.0 |  | intrinsic | error | ok | 4.31 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
_No data_

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
