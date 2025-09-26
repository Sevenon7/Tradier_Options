#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reads overlay_vwap_macd_rsi.csv, computes intraday VWAP for each ticker using Tradier timesales,
sets VWAP and Px_vs_VWAP, and writes back in-place (graceful if timesales returns empty).

Usage:
  python tools/enrich_overlay_with_vwap.py [--overlay overlay_vwap_macd_rsi.csv]

Env:
  TRADIER_TOKEN  -> Bearer token for production (required for live VWAP; otherwise leaves as Unknown)
"""

from __future__ import annotations
import argparse, os, sys
import pandas as pd
from tools.vwap_utils import compute_today_vwap

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--overlay", default="overlay_vwap_macd_rsi.csv")
    args = ap.parse_args()

    path = args.overlay
    if not os.path.exists(path):
        print(f"[enrich] overlay file not found: {path} (skipping)")
        return 0

    df = pd.read_csv(path)
    # Ensure required columns exist
    if "Ticker" not in df.columns:
        print("[enrich] 'Ticker' column missing in overlay CSV (skipping)")
        return 0
    if "LastPx" not in df.columns:
        df["LastPx"] = None

    # Compute VWAP per ticker (graceful if token missing or endpoint returns empty)
    vwap_vals = []
    px_vs = []
    for _, row in df.iterrows():
        ticker = str(row["Ticker"]).strip()
        lastpx = None
        try:
            lastpx = float(row["LastPx"])
        except Exception:
            lastpx = None

        vwap = compute_today_vwap(ticker)
        vwap_vals.append(vwap)

        if vwap is None or lastpx is None:
            px_vs.append("Unknown")
        else:
            px_vs.append("Above" if lastpx >= vwap else "Below")

    # Overwrite/insert columns
    df["VWAP"] = vwap_vals
    df["Px_vs_VWAP"] = px_vs

    # Persist in-place
    df.to_csv(path, index=False)
    print(f"[enrich] overlay updated with VWAP for {len(df)} tickers: {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
