#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust Option P/L CSV builder for Tradier.
- Per-symbol calls (so one bad OCC never nukes the batch).
- Fallback mid: (bid+ask)/2 → last → intrinsic floor using underlying spot.
- OCC parsing with correct 5+3 strike decoding.
- Always writes option_pl.csv (even if partial), with audit columns.

Env:
  TRADIER_TOKEN  -> required for live quotes (for mid/last; intrinsic still works without).
"""

from __future__ import annotations
import os, re, time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

import requests
import pandas as pd

TRADIER_BASE = "https://api.tradier.com"
HDRS = lambda tok: {"Authorization": f"Bearer {tok}", "Accept": "application/json"}

RETRY_ATTEMPTS = 3
RETRY_SLEEP = 0.8

@dataclass
class OCCParts:
    root: str
    y: int
    m: int
    d: int
    cp: str  # 'C' or 'P'
    strike: float

def parse_occ(occ: str) -> Optional[OCCParts]:
    """
    OCC: ROOT + YYMMDD + C/P + STRIKE(8 digits; first 5=dollars, last 3=.000)
    META260220C00700000 -> root=META, y=2026, m=02, d=20, cp=C, strike=700.000
    MSTU260320C00005000 -> root=MSTU, y=2026, m=03, d=20, cp=C, strike=5.000
    """
    m = re.match(r"^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$", occ)
    if not m:
        return None
    root, yy, mo, dd, cp, strike8 = m.groups()
    dollars = int(strike8[:5])
    millis  = int(strike8[5:])
    strike  = dollars + millis / 1000.0
    y = 2000 + int(yy)
    return OCCParts(root=root, y=y, m=int(mo), d=int(dd), cp=cp, strike=strike)

def _get(url: str, headers: dict, params: dict | None = None) -> Tuple[int, Optional[dict]]:
    last_err = None
    for i in range(RETRY_ATTEMPTS):
        try:
            r = requests.get(url, headers=headers, params=params or {}, timeout=10)
            if r.status_code == 200:
                try:
                    return r.status_code, r.json()
                except Exception:
                    return r.status_code, None
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
        time.sleep(RETRY_SLEEP * (i + 1))
    return 0, {"error": last_err} if last_err else None

def fetch_option_quote(token: str, occ: str) -> Tuple[str, Optional[dict]]:
    """Returns (status, quote_json_or_None). status in {'ok','not_found','error'}."""
    url = f"{TRADIER_BASE}/v1/markets/options/quotes"
    code, js = _get(url, HDRS(token), params={"symbols": occ, "greeks": "true"})
    if code == 200 and js:
        q = js.get("quotes", {}).get("quote")
        if isinstance(q, list):
            q = q[0] if q else None
        return ("ok", q) if q else ("not_found", None)
    if code == 404:
        return "not_found", None
    return "error", None

def fetch_underlying_spot(token: str, symbol: str) -> Tuple[str, Optional[float]]:
    url = f"{TRADIER_BASE}/v1/markets/quotes"
    code, js = _get(url, HDRS(token), params={"symbols": symbol})
    if code == 200 and js:
        q = js.get("quotes", {}).get("quote")
        if isinstance(q, list):
            q = q[0] if q else None
        if q:
            for k in ("last", "close", "bid", "ask"):
                v = q.get(k)
                try:
                    if v is not None:
                        return "ok", float(v)
                except Exception:
                    pass
    return ("error", None)

def compute_mid_source(quote: Optional[dict], cp: str, strike: float, spot: Optional[float]) -> Tuple[Optional[float], str]:
    """
    mid = (bid+ask)/2 if both
        else last
        else intrinsic floor against spot (if available)
        else None
    """
    if quote:
        bid = quote.get("bid"); ask = quote.get("ask"); last = quote.get("last")
        try:
            if bid is not None and ask is not None and float(bid) > 0 and float(ask) > 0:
                return ((float(bid) + float(ask)) / 2.0, "mid")
        except Exception:
            pass
        try:
            if last is not None and float(last) >= 0:
                return (float(last), "last")
        except Exception:
            pass
    if spot is not None:
        intrinsic = max(0.0, (spot - strike)) if cp == "C" else max(0.0, (strike - spot))
        return (intrinsic, "intrinsic")
    return (None, "none")

def round_or_none(x, n: int = 2):
    try:
        return round(float(x), n)
    except Exception:
        return None

def build_option_pl(open_options: List[Dict[str, Any]], out_csv: str = "option_pl.csv") -> pd.DataFrame:
    """
    open_options item: {"label","occ","entry","contracts"}
    Writes out_csv and returns DataFrame (never leaves missing file).
    """
    token = os.environ.get("TRADIER_TOKEN", "").strip()
    rows: List[Dict[str, Any]] = []

    for o in open_options:
        label = o.get("label",""); occ = o.get("occ","")
        entry = float(o.get("entry",0)); qty = int(o.get("contracts",0))

        parts = parse_occ(occ)
        if not parts:
            rows.append({
                "Contract": label, "OCC": occ, "Bid": None, "Ask": None, "Last": None,
                "MidUsed": None, "Entry": entry, "Contracts": qty, "P/L($)": None, "P/L(%)": None,
                "IV": None, "source": "invalid_occ", "quote_status": "n/a", "spot_status":"n/a",
                "spot": None, "strike": None, "type": None, "root": None, "expiry": None,
                "note": "Failed to parse OCC"
            })
            continue

        # Option quote
        quote_status, q = ("no_token", None)
        if token:
            quote_status, q = fetch_option_quote(token, occ)

        # Underlying spot (for intrinsic floor)
        spot_status, spot = ("no_token", None)
        if token:
            spot_status, spot = fetch_underlying_spot(token, parts.root)

        # Compute mid with fallbacks
        mid, source = compute_mid_source(q, parts.cp, parts.strike, spot)

        # Greeks IV if available
        iv = None
        if q:
            greeks = q.get("greeks") or {}
            iv = greeks.get("iv") or q.get("iv")

        pl_d = pl_p = None
        if mid is not None:
            pl_d = (mid - entry) * 100.0 * qty
            pl_p = (mid / entry - 1.0) * 100.0 if entry else None

        rows.append({
            "Contract": label,
            "OCC": occ,
            "Bid": round_or_none(q.get("bid")) if q else None,
            "Ask": round_or_none(q.get("ask")) if q else None,
            "Last": round_or_none(q.get("last")) if q else None,
            "MidUsed": round_or_none(mid),
            "Entry": round_or_none(entry),
            "Contracts": qty,
            "P/L($)": round_or_none(pl_d),
            "P/L(%)": round_or_none(pl_p),
            "IV": round_or_none(iv, 4) if iv is not None else None,
            "source": source,              # mid / last / intrinsic / none
            "quote_status": quote_status,  # ok / not_found / error / no_token
            "spot_status": spot_status,    # ok / error / no_token
            "spot": round_or_none(spot),
            "strike": round_or_none(parts.strike, 3),
            "type": "CALL" if parts.cp == "C" else "PUT",
            "root": parts.root,
            "expiry": f"{parts.y:04d}-{parts.m:02d}-{parts.d:02d}",
            "note": None if source != "none" else "No quote and no spot; unable to value"
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)  # ALWAYS write CSV
    return df

if __name__ == "__main__":
    OPEN_OPTIONS = [
        {"label": "META 700C Feb '26", "occ": "META260220C00700000", "entry": 109.13, "contracts": 1},
        {"label": "MSTU 5C Mar '26",  "occ": "MSTU260320C00005000", "entry": 1.86,  "contracts": 20},
    ]
    build_option_pl(OPEN_OPTIONS, out_csv="option_pl.csv")
