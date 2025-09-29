# Analysis Digest

**date_dir:** `data/2025-09-29`  
**generated_utc:** 2025-09-29T18:13:12Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-29/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-29/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-29/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-29/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 63.77 | True | 162.5595 | 163.0087 | Above | 145.8837 | 0.41 | HOLD |
| ASTS | 75.44 | True | 50.6709 | 49.8733 | Below | 42.5857 | 1.77 | TRIM |
| BBAI | 67.99 | True | 6.5778 | 6.5277 | Below | 5.531 | 2.08 | TRIM |
| META | 38.53 | False | 746.8408 | 743.08 | Below | 716.5048 | 0.67 | EXIT |
| MSFT | 64.31 | True | 514.4107 | 514.225 | Below | 493.8181 | 0.01 | TRIM |
| MSTR | 48.9 | True | 320.9547 | 325.945 | Above | 377.8068 | 1.51 | HOLD |
| MSTU | 46.2 | True | 4.6218 | 4.765 | Above | 7.3971 | 3.02 | HOLD |
| NVDA | 64.08 | True | 182.6466 | 181.9956 | Below | 161.0327 | 1.25 | TRIM |
| PLTR | 68.72 | True | 179.0695 | 178.55 | Below | 150.0116 | 1.17 | TRIM |
| QQQ | 73.54 | True | 599.9691 | 598.94 | Below | 554.1796 | 0.53 | TRIM |
| RDDT | 50.27 | False | 243.1207 | 240.6836 | Below | 172.2177 | 1.95 | TRIM |
| RKLB | 50.29 | False | 47.2171 | 47.2 | Below | 38.6754 | 2.46 | TRIM |
| UUUU | 68.82 | True | 16.6347 | 16.22 | Below | 8.5609 | 3.35 | TRIM |
| VST | 56.25 | False | 202.7823 | 202.695 | Below | 186.6428 | -2.52 | TRIM |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 43.11 | 109.13 | 1 | -6602.0 | -60.5 |  | intrinsic | error | ok | 743.11 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.0 | 1.86 | 20 | -3720.0 | -100.0 |  | intrinsic | error | ok | 4.77 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
| Ticker | Gap% | Close | SMA100 |
| --- | --- | --- | --- |
| VST | -2.52 | 202.695 | 186.64284 |

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
