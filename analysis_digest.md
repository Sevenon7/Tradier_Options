# Analysis Digest

**date_dir:** `data/2025-09-25`  
**generated_utc:** 2025-09-25T00:31:07Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-25/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-25/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-25/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-25/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 48.73 | True |  | 160.88 | Unknown | 144.0264 | 1.29 | HOLD |
| ASTS | 74.96 | True |  | 54.5 | Unknown | 41.8648 | 0.33 | HOLD |
| BBAI | 83.59 | True |  | 7.59 | Unknown | 5.4236 | 0.63 | HOLD |
| META | 56.12 | False |  | 760.66 | Unknown | 711.9829 | 0.28 | HOLD |
| MSFT | 51.78 | True |  | 510.15 | Unknown | 491.5387 | 0.23 | HOLD |
| MSTR | 47.49 | True |  | 323.31 | Unknown | 380.1148 | 0.87 | HOLD |
| MSTU | 44.9 | True |  | 4.76 | Unknown | 7.5234 | 1.73 | HOLD |
| NVDA | 56.14 | True |  | 176.97 | Unknown | 159.0726 | 0.75 | HOLD |
| PLTR | 72.29 | True |  | 179.56 | Unknown | 148.2284 | 0.75 | HOLD |
| QQQ | 78.64 | True |  | 596.1 | Unknown | 550.857 | 0.23 | HOLD |
| RDDT | 51.68 | False |  | 235.69 | Unknown | 168.4838 | 1.71 | HOLD |
| RKLB | 58.73 | True |  | 48.69 | Unknown | 37.9528 | -2.11 | HOLD |
| UUUU | 82.19 | True |  | 16.87 | Unknown | 8.1967 | 3.96 | HOLD |
| VST | 59.03 | True |  | 202.06 | Unknown | 184.7683 | -0.48 | HOLD |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 60.66 | 109.13 | 1 | -4847.0 | -44.41 |  | intrinsic | error | ok | 760.66 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.0 | 1.86 | 20 | -3720.0 | -100.0 |  | intrinsic | error | ok | 4.76 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
| Ticker | Gap% | Close | SMA100 |
| --- | --- | --- | --- |
| RKLB | -2.11 | 48.69 | 37.95275 |

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
