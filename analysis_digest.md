# Analysis Digest

**date_dir:** `data/2025-09-30`  
**generated_utc:** 2025-09-30T18:58:04Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-30/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-30/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-30/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-09-30/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 52.83 | True | 160.7196 | 160.75 | Above | 146.4711 | -0.35 | HOLD |
| ASTS | 73.82 | True | 48.5045 | 49.41 | Above | 42.8164 | -0.55 | HOLD |
| BBAI | 67.71 | True | 6.4906 | 6.4325 | Below | 5.5641 | -0.93 | TRIM |
| META | 39.43 | False | 731.8877 | 731.65 | Below | 717.856 | -0.15 | EXIT |
| MSFT | 65.32 | True | 514.7299 | 517.7548 | Above | 494.6664 | -0.26 | HOLD |
| MSTR | 47.44 | True | 319.3437 | 320.1101 | Above | 377.0889 | -1.71 | HOLD |
| MSTU | 44.89 | True | 4.5801 | 4.6002 | Above | 7.3556 | -3.14 | HOLD |
| NVDA | 61.79 | True | 185.3766 | 186.1651 | Above | 161.7224 | 0.13 | HOLD |
| PLTR | 67.61 | True | 180.1816 | 181.41 | Above | 150.7244 | 0.07 | HOLD |
| QQQ | 73.5 | True | 597.7063 | 599.025 | Above | 555.3351 | -0.05 | HOLD |
| RDDT | 32.16 | False | 229.0134 | 228.68 | Below | 173.4622 | -0.68 | EXIT |
| RKLB | 52.07 | False | 46.9958 | 47.4003 | Above | 38.9246 | 0.43 | HOLD |
| UUUU | 68.87 | True | 15.6049 | 15.77 | Above | 8.6742 | -8.41 | HOLD |
| VST | 38.92 | False | 193.8086 | 195.24 | Above | 187.1518 | 0.63 | HOLD |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 31.57 | 109.13 | 1 | -7756.0 | -71.07 |  | intrinsic | error | ok | 731.57 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.0 | 1.86 | 20 | -3720.0 | -100.0 |  | intrinsic | error | ok | 4.61 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
| Ticker | Gap% | Close | SMA100 |
| --- | --- | --- | --- |
| UUUU | -8.41 | 15.775 | 8.67415 |

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
