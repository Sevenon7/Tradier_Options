#!/usr/bin/env python3
"""
LEAPS Overlay Runner (Tradier) — resilient build

Enhancements:
- Retries + rate-limit awareness for all REST calls.
- Correct quotes endpoint for equities & OCC options (with greeks).
- Intraday VWAP via /v1/markets/timesales using ET cash session, fallback to 'all'.
- Market clock guard: VWAP set unavailable when the market is closed.
- Safe indicators (SMA100/RSI/MACD) only when enough bars.
- Gap screen empty-safe; atomic CSV writes; strict JSON-safe numbers.
"""

from __future__ import annotations
import os, sys, math, time, json, tempfile, contextlib, re
import datetime as dt
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# ---------- Config ----------
BASE   = "https://api.tradier.com/v1"
TOKEN  = os.getenv("TRADIER_TOKEN")
if not TOKEN:
    print("ERROR: Set TRADIER_TOKEN environment variable.")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

CONFIG = {
    "tickers": ["QQQ","META","MSFT","MSTU","MSTR","PLTR","AMD","NVDA","BBAI","RKLB","VST","ASTS","RDDT","UUUU"],
    "open_options": [
        {"occ":"META260220C00700000","entry":109.13,"contracts":1,  "label":"META 700C Feb '26"},
        {"occ":"MSTU260320C00005000","entry":1.86,  "contracts":20, "label":"MSTU 5C Mar '26"},
    ],
    "daily_lookback_days": 400,
    "intraday_interval": "5min",
    "out_overlay_csv": "overlay_vwap_macd_rsi.csv",
    "out_pl_csv": "option_pl.csv",
    "out_gap_csv": "gapdown_above_100sma.csv",
}

# ---------- Utils / resilience ----------
OSI_RE = re.compile(r"^[A-Z0-9 ]{6}\d{6}[CP]\d{8}$")  # 21-char OCC/OSI

def requests_retry_session(
    total=4, backoff_factor=0.6,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET"]),
    timeout=(4, 20)  # (connect, read)
) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=total, read=total, connect=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    original = s.request
    def _wrap(method, url, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = timeout
        return original(method, url, **kwargs)
    s.request = _wrap
    return s

S = requests_retry_session()

def _rate_limit_rest(resp: requests.Response):
    """Honor Tradier minute window if we're near empty."""
    if not resp:
        return
    hdr = {k.lower(): v for k, v in resp.headers.items()}
    # Tradier docs show 'X-Ratelimit-Available'/'X-Ratelimit-Expiry'
    remain = hdr.get("x-ratelimit-available") or hdr.get("x-ratelimit-remaining")
    expiry = hdr.get("x-ratelimit-expiry")
    try:
        remain_i = int(remain) if remain is not None else 2
        if remain_i <= 1 and expiry:
            now_ms = int(time.time() * 1000)
            exp_ms = int(expiry)
            if exp_ms > now_ms:
                sleep_s = min(5.0, (exp_ms - now_ms)/1000.0)
                time.sleep(max(0, sleep_s))
    except Exception:
        pass

def get_json(url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    r = S.get(url, headers=HEADERS, params=params or {})
    _rate_limit_rest(r)
    if r.status_code in (404,):
        print(f"[warn] 404: {url} {params}")
        return None
    if r.status_code in (401,):
        print("[error] 401 Unauthorized from Tradier. Check token scope.")
        return None
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        print(f"[warn] HTTP {r.status_code}: {url} {params} -> {e} :: {r.text[:200]}")
        return None
    try:
        return r.json()
    except ValueError:
        print(f"[warn] JSON decode failed: {url} {params}")
        return None

@contextlib.contextmanager
def atomic_write(path: str, mode: str = "w", encoding: str | None = "utf-8"):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=d)
    try:
        with os.fdopen(fd, mode, encoding=encoding, newline="") as f:
            yield f
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass

def safe_to_csv(df: pd.DataFrame, path: str):
    with atomic_write(path, mode="w", encoding="utf-8") as f:
        df.to_csv(f, index=False)

def sanitize_json(obj: Any) -> Any:
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    return obj

def validate_osi(occ: str) -> bool:
    return bool(OSI_RE.match(occ))

# ---------- TA helpers ----------
def rsi(series: pd.Series, period=14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    fast_ema, slow_ema = ema(series, fast), ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()

def session_vwap_from_bars(df: pd.DataFrame):
    if df is None or df.empty:
        return math.nan, math.nan
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df["volume"].fillna(0)
    cv = vol.cumsum()
    vwap = (tp * vol).cumsum() / cv.replace(0, pd.NA)
    last_px = float(df["close"].iloc[-1])
    return (float(vwap.iloc[-1]) if pd.notna(vwap.iloc[-1]) else math.nan, last_px)

def mid_from_quote(q: dict) -> float:
    bid = float(q.get("bid") or 0)
    ask = float(q.get("ask") or 0)
    last = float(q.get("last") or 0)
    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0
    return last or bid or ask

# ---------- Tradier pulls ----------
def market_open_now() -> bool | None:
    data = get_json(f"{BASE}/markets/clock")
    if not data or "clock" not in data:
        # fail soft (assume open in case clock temporarily unavailable)
        return None
    return data["clock"].get("state") == "open"

def get_daily_history(symbol: str, start: str, end: str) -> pd.DataFrame:
    data = get_json(f"{BASE}/markets/history",
                    params={"symbol": symbol, "interval": "daily", "start": start, "end": end})
    rows = (data or {}).get("history", {}).get("day", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("date")

def get_intraday_timesales(symbol: str, start_dt_et: dt.datetime, end_dt_et: dt.datetime,
                           interval="5min", session="open") -> pd.DataFrame:
    fmt = "%Y-%m-%d %H:%M"
    data = get_json(f"{BASE}/markets/timesales", params={
        "symbol": symbol,
        "interval": interval,
        "start": start_dt_et.strftime(fmt),
        "end": end_dt_et.strftime(fmt),
        "session_filter": session
    })
    rows = (data or {}).get("series", {}).get("data", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"])
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("time")

def batch_equity_quotes(symbols: List[str]) -> dict:
    data = get_json(f"{BASE}/markets/quotes", params={"symbols": ",".join(symbols)})
    q = (data or {}).get("quotes", {}).get("quote", [])
    if isinstance(q, dict):
        q = [q]
    return {row.get("symbol"): row for row in q if isinstance(row, dict)}

def options_quotes_occ(occs: List[str]) -> dict:
    good = [o for o in occs if validate_osi(o)]
    bad = [o for o in occs if not validate_osi(o)]
    for b in bad:
        print(f"[warn] OCC symbol failed OSI check: {b}")

    # Batch first
    params = {"symbols": ",".join(good), "greeks": "true"} if good else {"symbols": "", "greeks": "true"}
    data = get_json(f"{BASE}/markets/quotes", params=params)
    out = {}
    if data:
        rows = data.get("quotes", {}).get("quote", [])
        if isinstance(rows, dict): rows = [rows]
        for r in rows:
            if isinstance(r, dict) and r.get("symbol"):
                out[r["symbol"]] = r

    # Per-symbol salvage
    for occ in good:
        if occ in out:
            continue
        d = get_json(f"{BASE}/markets/quotes", params={"symbols": occ, "greeks": "true"})
        if not d: 
            continue
        rows = d.get("quotes", {}).get("quote", [])
        if isinstance(rows, dict): rows = [rows]
        for r in rows:
            if r.get("symbol") == occ:
                out[occ] = r
                break
    return out

# ---------- Main ----------
def main():
    # Time anchors
    now_utc = dt.datetime.now(dt.timezone.utc)
    et = ZoneInfo("America/New_York")
    now_et = now_utc.astimezone(et)
    session_open_et = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    if now_et < session_open_et:
        session_open_et = session_open_et  # today 09:30 ET
    session_end_et = now_et

    # Daily window
    start_hist = (now_et - dt.timedelta(days=CONFIG["daily_lookback_days"])).strftime("%Y-%m-%d")
    end_hist   = now_et.strftime("%Y-%m-%d")

    # Market clock (None = unknown)
    is_open = market_open_now()

    # Equity quotes
    quotes = batch_equity_quotes(CONFIG["tickers"])

    # Daily frames (for indicators)
    daily_frames: dict[str, pd.DataFrame] = {}
    for sym in CONFIG["tickers"]:
        df = get_daily_history(sym, start_hist, end_hist)
        daily_frames[sym] = df

    overlay_rows, gap_rows = [], []

    for sym, ddf in daily_frames.items():
        if ddf.empty or len(ddf) < 2:
            print(f"[warn] insufficient daily data for {sym}")
            continue

        ddf["SMA100"] = sma(ddf["close"], 100)
        ddf["RSI14"]  = rsi(ddf["close"], 14)
        macd_line, sig_line, _ = macd(ddf["close"], 12, 26, 9)
        ddf["MACD"], ddf["MACDsig"] = macd_line, sig_line

        last = ddf.iloc[-1]
        prev = ddf.iloc[-2]

        # Gap%
        gap_pct = None
        if pd.notna(prev["close"]) and prev["close"] > 0 and pd.notna(last["open"]):
            gap_pct = (float(last["open"]) - float(prev["close"])) / float(prev["close"]) * 100.0

        # Intraday VWAP (only if open/unknown)
        vwap = math.nan
        last_px_intraday = math.nan
        if is_open is None or is_open is True:
            idf = get_intraday_timesales(sym, session_open_et, session_end_et,
                                         interval=CONFIG["intraday_interval"], session="open")
            if idf.empty:
                alt_start = session_open_et - dt.timedelta(minutes=5)
                idf = get_intraday_timesales(sym, alt_start, session_end_et,
                                             interval=CONFIG["intraday_interval"], session="all")
            vwap, last_px_intraday = session_vwap_from_bars(idf)

        last_px = (last_px_intraday if last_px_intraday == last_px_intraday
                   else float(quotes.get(sym, {}).get("last") or last["close"]))
        above_vwap = None
        if not math.isnan(vwap) and last_px == last_px:
            try:
                above_vwap = float(last_px) > float(vwap)
            except Exception:
                above_vwap = None

        macd_pos = bool(last["MACD"] > last["MACDsig"])
        rsi_val  = float(last["RSI14"]) if pd.notna(last["RSI14"]) else None

        # Heuristic guidance
        if (above_vwap is False) and (not macd_pos) and (rsi_val is not None and rsi_val < 45):
            guidance = "EXIT"
        elif (above_vwap is False) or (rsi_val is not None and rsi_val > 70 and not macd_pos):
            guidance = "TRIM"
        else:
            guidance = "HOLD"

        overlay_rows.append({
            "Ticker": sym,
            "RSI14": round(rsi_val, 2) if rsi_val is not None else None,
            "MACD>Signal": macd_pos,
            "VWAP": (None if math.isnan(vwap) else round(float(vwap), 4)),
            "LastPx": round(float(last_px), 4) if last_px == last_px else None,
            "Px_vs_VWAP": ("Above" if above_vwap else ("Below" if above_vwap is False else "Unknown")),
            "SMA100": round(float(last["SMA100"]), 4) if pd.notna(last["SMA100"]) else None,
            "Gap%": round(gap_pct, 2) if gap_pct is not None else None,
            "Guidance": guidance,
            "MarketOpen": is_open if is_open is not None else "unknown"
        })

        # Gap screen row
        if (gap_pct is not None and gap_pct <= -1.0) and (float(last["close"]) > float(last["SMA100"])):
            gap_rows.append({
                "Ticker": sym,
                "Gap%": round(gap_pct, 2),
                "Close": float(last["close"]),
                "SMA100": float(last["SMA100"])
            })

    # Options P/L via OCC symbols
    occs = [o["occ"] for o in CONFIG["open_options"]]
    occ_quotes = options_quotes_occ(occs)

    pl_rows = []
    for o in CONFIG["open_options"]:
        if not validate_osi(o["occ"]):
            print(f"[warn] skipping invalid OCC: {o['occ']}")
            continue
        q = occ_quotes.get(o["occ"], {})
        if not q:
            print(f"[warn] missing quote for {o['occ']}; skipping P/L calc")
            continue
        mid = mid_from_quote(q)
        pnl_d = (mid - o["entry"]) * 100 * o["contracts"]
        pnl_p = (mid / o["entry"] - 1) * 100 if o["entry"] else None
        iv = None
        g = (q.get("greeks") or {})
        # Tradier reference lists greeks.* fields including IV; keep graceful if absent
        iv = g.get("mid_iv") or g.get("ask_iv") or g.get("bid_iv") or g.get("smv_vol")

        pl_rows.append({
            "Contract": o["label"],
            "OCC": o["occ"],
            "Bid": q.get("bid"),
            "Ask": q.get("ask"),
            "Last": q.get("last"),
            "MidUsed": round(mid, 2) if mid == mid else None,
            "Entry": o["entry"],
            "Contracts": o["contracts"],
            "P/L($)": round(pnl_d, 2) if pnl_p is not None else None,
            "P/L(%)": round(pnl_p, 2) if pnl_p is not None else None,
            "IV": iv
        })

    # ---------- Save outputs (atomic, empty-safe) ----------
    overlay_cols = ["Ticker","RSI14","MACD>Signal","VWAP","LastPx","Px_vs_VWAP","SMA100","Gap%","Guidance","MarketOpen"]
    pl_cols      = ["Contract","OCC","Bid","Ask","Last","MidUsed","Entry","Contracts","P/L($)","P/L(%)","IV"]
    gap_cols     = ["Ticker","Gap%","Close","SMA100"]

    df_overlay = pd.DataFrame(overlay_rows)
    if df_overlay.empty:
        df_overlay = pd.DataFrame(columns=overlay_cols)
    else:
        df_overlay = df_overlay[[c for c in overlay_cols if c in df_overlay.columns]]
        df_overlay = df_overlay.sort_values("Ticker", na_position="last")
    safe_to_csv(df_overlay, CONFIG["out_overlay_csv"])

    df_pl = pd.DataFrame(pl_rows)
    if df_pl.empty:
        df_pl = pd.DataFrame(columns=pl_cols)
    else:
        df_pl = df_pl[[c for c in pl_cols if c in df_pl.columns]]
    safe_to_csv(df_pl, CONFIG["out_pl_csv"])

    df_gap = pd.DataFrame(gap_rows)
    if df_gap.empty:
        df_gap = pd.DataFrame(columns=gap_cols)
    else:
        if "Gap%" in df_gap.columns:
            df_gap["Gap%"] = pd.to_numeric(df_gap["Gap%"], errors="coerce")
            df_gap = df_gap.sort_values("Gap%", na_position="last")
        df_gap = df_gap[[c for c in gap_cols if c in df_gap.columns]]
    safe_to_csv(df_gap, CONFIG["out_gap_csv"])

    # Pretty logs
    print("\n=== OVERLAY (VWAP / MACD / RSI) ===")
    try: print(df_overlay.to_string(index=False))
    except Exception: print("(overlay not available)")

    print("\n=== ACTUAL OPTION P/L (mid used) ===")
    try: print(df_pl.to_string(index=False))
    except Exception: print("(option P/L not available)")

    print("\n=== GAP DOWN ≥ -1% & ABOVE 100-SMA ===")
    try: print(df_gap.to_string(index=False))
    except Exception: print("(gap screen not available)")

if __name__ == "__main__":
    main()
