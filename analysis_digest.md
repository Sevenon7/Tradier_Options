# Analysis Digest

**date_dir:** `data/2025-10-06`  
**generated_utc:** 2025-10-06T17:55:11Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-06/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-06/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-06/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-06/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 85.18 | True | 212.6774 | 207.86 | Below | 149.292 | 37.51 | TRIM |
| ASTS | 87.02 | True | 71.7511 | 74.44 | Above | 44.4189 | 2.07 | HOLD |
| BBAI | 67.5 | True | 7.5303 | 7.67 | Above | 5.7239 | 0.7 | HOLD |
| META | 19.72 | False | 701.5846 | 712.75 | Above | 721.6997 | -0.76 | HOLD |
| MSFT | 67.91 | True | 523.6356 | 528.325 | Above | 497.7272 | 0.24 | HOLD |
| MSTR | 58.12 | True | 359.7869 | 357.8957 | Below | 374.5418 | 3.22 | TRIM |
| MSTU | 56.41 | True | 5.752 | 5.68 | Below | 7.1857 | 6.35 | TRIM |
| NVDA | 63.47 | True | 185.7534 | 185.59 | Below | 164.3505 | -1.13 | TRIM |
| PLTR | 58.02 | False | 180.548 | 179.47 | Below | 153.1489 | 3.53 | TRIM |
| QQQ | 70.66 | True | 607.5239 | 608.66 | Above | 559.5594 | 0.87 | HOLD |
| RDDT | 22.39 | False | 205.0411 | 210.3 | Above | 177.2821 | 0.05 | HOLD |
| RKLB | 71.16 | True | 57.2869 | 58.25 | Above | 40.2118 | 1.26 | HOLD |
| UUUU | 73.54 | False | 17.5583 | 17.355 | Below | 9.1468 | 5.02 | TRIM |
| VST | 43.11 | False | 201.2402 | 202.31 | Above | 189.4666 | 2.06 | HOLD |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 12.9 | 109.13 | 1 | -9623.0 | -88.18 |  | intrinsic | error | ok | 712.9 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.68 | 1.86 | 20 | -2350.0 | -63.17 |  | intrinsic | error | ok | 5.68 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
| Ticker | Gap% | Close | SMA100 |
| --- | --- | --- | --- |
| NVDA | -1.13 | 185.595 | 164.35045 |

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
