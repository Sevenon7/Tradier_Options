#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick probe to check /v1/markets/timesales availability for your token/plan.
Tries production with TRADIER_TOKEN. If TRADIER_SANDBOX_TOKEN is set, also tries sandbox.

Usage:
  python tools/timesales_probe.py META
"""

from __future__ import annotations
import os, sys, datetime as dt
import requests
from zoneinfo import ZoneInfo

def try_timesales(base: str, token: str, symbol: str) -> tuple[int, str]:
    tz_et = ZoneInfo("America/New_York")
    now = dt.datetime.now(tz=tz_et)
    start = now.replace(hour=9, minute=30, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")
    end   = now.strftime("%Y-%m-%d %H:%M")
    url = f"{base}/v1/markets/timesales"
    hdr = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {"symbol": symbol, "interval": "1min", "start": start, "end": end, "session_filter": "open"}
    try:
        r = requests.get(url, headers=hdr, params=params, timeout=15)
        if r.status_code != 200:
            return r.status_code, f"HTTP {r.status_code}: {r.text[:200]}"
        js = r.json()
        n = len((js or {}).get("series", {}).get("data", []) or [])
        return 200, f"OK, points={n}"
    except Exception as e:
        return 0, str(e)

def main():
    if len(sys.argv) < 2:
        print("usage: python tools/timesales_probe.py <SYMBOL>")
        return 2
    sym = sys.argv[1].upper()

    prod_token = os.environ.get("TRADIER_TOKEN", "").strip()
    sand_token = os.environ.get("TRADIER_SANDBOX_TOKEN", "").strip()

    if prod_token:
        code, msg = try_timesales("https://api.tradier.com", prod_token, sym)
        print(f"[prod] {sym}: {msg}")
    else:
        print("[prod] TRADIER_TOKEN not set")

    if sand_token:
        code, msg = try_timesales("https://sandbox.tradier.com", sand_token, sym)
        print(f"[sandbox] {sym}: {msg}")
    else:
        print("[sandbox] TRADIER_SANDBOX_TOKEN not set")

if __name__ == "__main__":
    sys.exit(main())
