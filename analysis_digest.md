# Analysis Digest

**date_dir:** `data/2025-10-01`  
**generated_utc:** 2025-10-01T23:02:12Z  
**latest.json:** https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/latest.json

### Raw links

- overlay: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-01/overlay_vwap_macd_rsi.csv
- option_pl: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-01/option_pl.csv
- gap_screen: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-01/gapdown_above_100sma.csv
- ready: https://raw.githubusercontent.com/Sevenon7/Tradier_Options/main/data/2025-10-01/READY

## Overlay (VWAP/MACD/RSI)
| Ticker | RSI14 | MACD>Signal | VWAP | LastPx | Px_vs_VWAP | SMA100 | Gap% | Guidance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD | 71.34 | True | 162.5437 | 164.01 | Above | 147.1046 | -0.53 | HOLD |
| ASTS | 79.41 | True | 54.8808 | 56.94 | Above | 43.13 | 9.03 | HOLD |
| BBAI | 70.41 | True | 6.8429 | 6.98 | Above | 5.6023 | 0.46 | HOLD |
| META | 34.65 | False | 716.8932 | 717.34 | Above | 719.0765 | -1.76 | HOLD |
| MSFT | 66.09 | True | 516.2274 | 519.71 | Above | 495.4834 | -0.61 | HOLD |
| MSTR | 54.56 | True | 338.6381 | 338.41 | Below | 376.3492 | 3.18 | HOLD |
| MSTU | 52.2 | True | 5.1302 | 5.11 | Below | 7.3095 | 6.02 | HOLD |
| NVDA | 63.11 | True | 186.5809 | 187.24 | Above | 162.4252 | -0.72 | HOLD |
| PLTR | 74.01 | True | 184.0364 | 184.95 | Above | 151.3922 | -0.61 | HOLD |
| QQQ | 74.04 | True | 601.0808 | 603.25 | Above | 556.4979 | -0.53 | HOLD |
| RDDT | 23.57 | False | 208.8999 | 202.6 | Below | 174.423 | -7.39 | HOLD |
| RKLB | 49.19 | False | 48.4325 | 47.97 | Below | 39.1782 | -1.11 | HOLD |
| UUUU | 67.63 | True | 15.3417 | 15.71 | Above | 8.7794 | -2.28 | HOLD |
| VST | 47.99 | False | 200.8786 | 201.51 | Above | 187.7655 | -0.47 | HOLD |

## Actual Option P/L
| Contract | OCC | Bid | Ask | Last | MidUsed | Entry | Contracts | P/L($) | P/L(%) | IV | source | quote_status | spot_status | spot | strike | type | root | expiry | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META 700C Feb '26 | META260220C00700000 |  |  |  | 17.34 | 109.13 | 1 | -9179.0 | -84.11 |  | intrinsic | error | ok | 717.34 | 700.0 | CALL | META | 2026-02-20 |  |
| MSTU 5C Mar '26 | MSTU260320C00005000 |  |  |  | 0.11 | 1.86 | 20 | -3500.0 | -94.09 |  | intrinsic | error | ok | 5.11 | 5.0 | CALL | MSTU | 2026-03-20 |  |

## Gap Down ≥ -1% & Above 100-SMA
| Ticker | Gap% | Close | SMA100 |
| --- | --- | --- | --- |
| RDDT | -7.39 | 202.6 | 174.423 |
| UUUU | -2.28 | 15.71 | 8.7794 |
| RKLB | -1.11 | 47.97 | 39.17825 |

### Notes
- Pointer freshness <=24h: True
- READY flag present: False
