# LEAPS Overlay Runner (Tradier, Batched + Cached)

This script pulls **batch quotes**, **daily OHLCV (cached once/day)**, **intraday 5-minute bars** for session VWAP, and **options quotes** for your open LEAPS. It then computes **RSI(14)**, **MACD(12/26/9)**, **SMA(100)**, a gap-down screen, and **Actual option P/L** using **mid = (bid+ask)/2** (fallback to `last` if one-sided).

## Files produced
- `overlay_vwap_macd_rsi.csv`
- `option_pl.csv`
- `gapdown_above_100sma.csv`

## How to run
```bash
pip install requests pandas pyarrow

# Set your token securely
export TRADIER_TOKEN='YOUR_TOKEN'   # PowerShell: $env:TRADIER_TOKEN='YOUR_TOKEN'

python leaps_batched_cached.py
