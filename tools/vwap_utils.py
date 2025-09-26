#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VWAP helpers using Tradier /v1/markets/timesales.
- Computes intraday VWAP from market open (09:30 ET) up to "now" ET.
- Graceful retries and empty-data handling.
Env:
  TRADIER_TOKEN   -> Bearer token for production (required for live data).
"""

from __future__ import annotations
import os, time
from typing import Optional
from zoneinfo import ZoneInfo
import datetime as dt
import requests
import pandas as pd

TRADIER = "https://api.tradier.com"
HEADERS = lambda tok: {"Authorization": f"Bearer {tok}", "Accept": "application/json"}

def _get_json(url: str, token: str, params: dict, retries: int = 3, backoff: float = 1.2) -> tuple[int, dict|None]:
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS(token), params=params, timeout=15)
            if r.status_code == 200:
                try:
                    return r.status_code, r.json()
                except Exception:
                    return r.status_code, None
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
        time.sleep(backoff * (i+1))
    return 0, {"error": last_err} if last_err else None

def fetch_timesales(symbol: str, start_et: str, end_et: str, interval: str = "1min") -> pd.DataFrame:
    """
    start_et/end_et: 'YYYY-MM-DD HH:MM' in America/New_York (ET)
    Returns DataFrame[time, price, volume] or empty df.
    """
    token = os.environ.get("TRADIER_TOKEN", "").strip()
    if not token:
        return pd.DataFrame()
    url = f"{TRADIER}/v1/markets/timesales"
    params = {"symbol": symbol, "interval": interval, "start": start_et, "end": end_et, "session_filter": "open"}
    code, js = _get_json(url, token, params)
    if code != 200 or not js:
        return pd.DataFrame()
    series = (js or {}).get("series", {}).get("data", [])
    if not series:
        return pd.DataFrame()
    df = pd.DataFrame(series)
    # Expecting keys: time, price, volume
    cols = [c for c in ["time", "price", "volume"] if c in df.columns]
    return df[cols].copy() if cols else pd.DataFrame()

def intraday_vwap(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "price" not in df or "volume" not in df:
        return None
    try:
        pv = (df["price"].astype(float) * df["volume"].astype(float)).sum()
        v  = df["volume"].astype(float).sum()
        return round(pv / v, 4) if v > 0 else None
    except Exception:
        return None

def compute_today_vwap(symbol: str, as_of_et: dt.datetime | None = None) -> Optional[float]:
    """
    Compute VWAP from 09:30 ET to "as_of_et" (ET). If not provided, uses current ET.
    """
    tz_et = ZoneInfo("America/New_York")
    as_of = as_of_et or dt.datetime.now(tz=tz_et)
    start = as_of.replace(hour=9, minute=30, second=0, microsecond=0)
    start_str = start.strftime("%Y-%m-%d %H:%M")
    end_str   = as_of.strftime("%Y-%m-%d %H:%M")
    df = fetch_timesales(symbol, start_str, end_str, interval="1min")
    return intraday_vwap(df)
