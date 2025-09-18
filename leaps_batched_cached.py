#!/usr/bin/env python3
"""
LEAPS Overlay Runner (Batched + Cached for Tradier)
- Fix: options quotes now use /v1/markets/quotes (works with OCC symbols)
- Fix: graceful handling for 404/HTTP errors; per-symbol fallback on batch failure
- Adds: light retry wrapper for transient 429/5xx
"""

import os, sys, math, time, json
import datetime as dt
import requests
import pandas as pd

BASE = "https://api.tradier.com/v1"
TOKEN = os.getenv("TRADIER_TOKEN")
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
    "session_start": "09:30",
    "session_end":   None,
    "interval": "5min",
    "out_overlay_csv": "overlay_vwap_macd_rsi.csv",
    "out_pl_csv": "option_pl.csv",
    "out_gap_csv": "gapdown_above_100sma.csv",
}

# ----------------- Helpers: indicators -----------------
def rsi(series: pd.Series, period=14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ema(series, span): return series.ewm(span=span, adjust=False).mean()

def macd(series, fast=12, slow=26, signal=9):
    fast_ema, slow_ema = ema(series, fast), ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line

def sma(series, period): return series.rolling(period).mean()

def session_vwap_from_bars(df):
    if df is None or df.empty: return math.nan, math.nan
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    vwap = (tp * df["volume"].fillna(0)).cumsum() / df["volume"].fillna(0).cumsum()
    return float(vwap.iloc[-1]), float(df["close"].iloc[-1])

def mid_from_quote(q):
    bid = float(q.get("bid") or 0)
    ask = float(q.get("ask") or 0)
    last = float(q.get("last") or 0)
    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0
    return last or bid or ask

# ----------------- Helpers: HTTP with retries -----------------
def _get_with_retry(url, params=None, headers=None, timeout=25, max_retries=3, backoff=0.8):
    """
    Light retry for 429/5xx. Returns (response or None, error_msg or None)
    """
    for attempt in range(1, max_retries+1):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                # Retry-able statuses
                wait = backoff * attempt
                print(f"[warn] HTTP {r.status_code} on {url}. Attempt {attempt}/{max_retries}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
                continue
            return r, None
        except requests.RequestException as e:
            wait = backoff * attempt
            print(f"[warn] RequestException on {url}: {e}. Attempt {attempt}/{max_retries}. Retrying in {wait:.1f}s...")
            time.sleep(wait)
    return None, f"Failed after {max_retries} attempts"

# ----------------- API: data pulls -----------------
def get_daily_history(symbol, start, end):
    url = f"{BASE}/markets/history"
    params = {"symbol":symbol,"interval":"daily","start":start,"end":end}
    r, err = _get_with_retry(url, params=params, headers=HEADERS, timeout=25)
    if err:
        print(f"[error] daily history retry failed for {symbol}: {err}")
        return pd.DataFrame()
    if r.status_code == 404:
        print(f"[error] 404 daily history for {symbol}: {r.url}")
        return pd.DataFrame()
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        print(f"[error] daily history HTTPError for {symbol}: {e} ({r.text[:200]})")
        return pd.DataFrame()
    data = r.json().get("history",{}).get("day",[])
    df = pd.DataFrame(data)
    if df.empty: return df
    df["date"]=pd.to_datetime(df["date"])
    for c in ["open","high","low","close","volume"]:
        df[c]=pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("date")

def get_intraday_timesales(symbol, start_dt, end_dt, interval="5min"):
    url = f"{BASE}/markets/timesales"
    params = {
        "symbol": symbol,
        "interval": interval,
        "start": start_dt.strftime("%Y-%m-%d %H:%M"),
        "end": end_dt.strftime("%Y-%m-%d %H:%M"),
        "session_filter": "all",
    }
    r, err = _get_with_retry(url, params=params, headers=HEADERS, timeout=25)
    if err:
        print(f"[warn] timesales retry failed for {symbol}: {err}")
        return pd.DataFrame()
    if r.status_code == 404:
        print(f"[warn] 404 timesales for {symbol}: {r.url}")
        return pd.DataFrame()
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        print(f"[warn] timesales HTTPError for {symbol}: {e} ({r.text[:200]})")
        return pd.DataFrame()
    data = r.json().get("series",{}).get("data",[])
    df = pd.DataFrame(data)
    if df.empty: return df
    df["time"]=pd.to_datetime(df["time"])
    for c in ["open","high","low","close","volume"]:
        df[c]=pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("time")

def batch_equity_quotes(symbols):
    url = f"{BASE}/markets/quotes"
    params = {"symbols": ",".join(symbols)}
    r, err = _get_with_retry(url, params=params, headers=HEADERS, timeout=20)
    if err:
        print(f"[warn] quotes retry failed: {err}")
        return {}
    if r.status_code == 404:
        print(f"[warn] 404 on batch quotes: {r.url}")
        return {}
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        print(f"[warn] quotes HTTPError: {e} ({r.text[:200]})")
        return {}
    q = r.json().get("quotes",{}).get("quote",[])
    if isinstance(q, dict): q=[q]
    return {row.get("symbol"): row for row in q if isinstance(row, dict)}

def options_quotes_occ(occs):
    """
    Correct endpoint for options quotes (OCC symbols): /v1/markets/quotes
    - Try batch first
    - On error (e.g., 404), fall back to per-symbol to salvage partial results
    Returns dict {occ_symbol: quote_dict}
    """
    url = f"{BASE}/markets/quotes"
    params = {"symbols": ",".join(occs), "greeks": "true"}

    # Try batch
    r, err = _get_with_retry(url, params=params, headers=HEADERS, timeout=20)
    if r and r.status_code == 200:
        try:
            data = r.json().get("quotes",{}).get("quote",[])
            if isinstance(data, dict): data = [data]
            out = {}
            for row in data:
                if not isinstance(row, dict): continue
                sym = row.get("symbol")
                if sym: out[sym] = row
            return out
        except Exception as e:
            print(f"[warn] parse error on batch options quotes: {e}")

    # If batch failed (or non-200), log and fall back per symbol
    code = r.status_code if r else "N/A"
    msg  = err or (r.text[:200] if r else "no response")
    print(f"[warn] batch options quotes failed (status={code}). Falling back per-symbol. Detail: {msg}")

    results = {}
    for occ in occs:
        pr, perr = _get_with_retry(url, params={"symbols":occ, "greeks":"true"}, headers=HEADERS, timeout=20)
        if not pr:
            print(f"[warn] options quote retry failed for {occ}: {perr}")
            continue
        if pr.status_code == 404:
            print(f"[warn] 404 for option symbol {occ}: {pr.url}")
            continue
        try:
            pr.raise_for_status()
        except requests.HTTPError as e:
            print(f"[warn] HTTPError for {occ}: {e} ({pr.text[:200]})")
            continue
        try:
            q = pr.json().get("quotes",{}).get("quote",[])
            if isinstance(q, dict): q=[q]
            # find the entry that matches our occ exactly (some APIs echo single)
            for row in q:
                if isinstance(row, dict) and row.get("symbol") == occ:
                    results[occ] = row
                    break
        except Exception as e:
            print(f"[warn] parse error for {occ}: {e}")
            continue
    return results

# ----------------- Main -----------------
def main():
    today = dt.datetime.now()
    start_date = (today - dt.timedelta(days=CONFIG["daily_lookback_days"])).strftime("%Y-%m-%d")
    end_date   = today.strftime("%Y-%m-%d")

    # Batch quotes for equities
    quotes = batch_equity_quotes(CONFIG["tickers"])

    # Daily bars (no-cached version here; safe in GH Actions once/day)
    daily_frames = {sym: get_daily_history(sym, start_date, end_date) for sym in CONFIG["tickers"]}

    overlay_rows, gap_rows = [], []
    session_start = dt.datetime.combine(today.date(), dt.datetime.strptime(CONFIG["session_start"], "%H:%M").time())
    session_end   = dt.datetime.now() if CONFIG["session_end"] is None else dt.datetime.combine(today.date(), dt.datetime.strptime(CONFIG["session_end"], "%H:%M").time())

    for sym, ddf in daily_frames.items():
        if ddf.empty or len(ddf) < 100:
            print(f"[warn] insufficient daily data for {sym}")
            continue

        ddf["SMA100"] = sma(ddf["close"], 100)
        ddf["RSI14"]  = rsi(ddf["close"], 14)
        macd_line, sig_line, _ = macd(ddf["close"], 12, 26, 9)
        ddf["MACD"], ddf["MACDsig"] = macd_line, sig_line

        last = ddf.iloc[-1]
        prev = ddf.iloc[-2] if len(ddf) >= 2 else None
        gap_pct = None
        if prev is not None and prev["close"] and prev["close"] > 0:
            gap_pct = (last["open"] - prev["close"]) / prev["close"] * 100.0

        try:
            idf = get_intraday_timesales(sym, session_start, session_end, interval=CONFIG["interval"])
        except Exception as e:
            print(f"[warn] intraday fetch failed for {sym}: {e}")
            idf = pd.DataFrame()

        vwap, last_px = session_vwap_from_bars(idf) if not idf.empty else (math.nan, quotes.get(sym,{}).get("last", math.nan))
        above_vwap = None
        try:
            if not math.isnan(vwap) and last_px == last_px:
                above_vwap = float(last_px) > float(vwap)
        except Exception:
            above_vwap = None

        macd_pos = bool(last["MACD"] > last["MACDsig"])
        rsi_val  = float(last["RSI14"]) if pd.notna(last["RSI14"]) else None

        if (above_vwap is False) and (not macd_pos) and (rsi_val is not None and rsi_val < 45): guidance="EXIT"
        elif (above_vwap is False) or (rsi_val is not None and rsi_val > 70 and not macd_pos):   guidance="TRIM"
        else: guidance="HOLD"

        overlay_rows.append({
            "Ticker": sym,
            "RSI14": round(rsi_val,2) if rsi_val is not None else None,
            "MACD>Signal": macd_pos,
            "VWAP": round(float(vwap),4) if vwap==vwap else None,
            "LastPx": round(float(last_px),4) if last_px==last_px else None,
            "Px_vs_VWAP": "Above" if above_vwap else ("Below" if above_vwap is False else "Unknown"),
            "SMA100": round(float(last["SMA100"]),4) if pd.notna(last["SMA100"]) else None,
            "Gap%": round(gap_pct,2) if gap_pct is not None else None,
            "Guidance": guidance
        })

        if (gap_pct is not None and gap_pct <= -1.0) and (float(last["close"]) > float(last["SMA100"])):
            gap_rows.append({
                "Ticker": sym,
                "Gap%": round(gap_pct,2),
                "Close": float(last["close"]),
                "SMA100": float(last["SMA100"])
            })

    # Options P/L (robust: batch, then per-symbol fallback)
    occs = [o["occ"] for o in CONFIG["open_options"]]
    occ_quotes = options_quotes_occ(occs)

    pl_rows = []
    for o in CONFIG["open_options"]:
        q = occ_quotes.get(o["occ"], {})
        if not q:
            print(f"[warn] missing quote for {o['occ']}; skipping P/L calc for this contract")
            continue
        mid = mid_from_quote(q)
        pnl_d = (mid - o["entry"]) * 100 * o["contracts"]
        pnl_p = (mid / o["entry"] - 1) * 100 if o["entry"] else None
        pl_rows.append({
            "Contract": o["label"],
            "OCC": o["occ"],
            "Bid": q.get("bid"),
            "Ask": q.get("ask"),
            "Last": q.get("last"),
            "MidUsed": round(mid,2),
            "Entry": o["entry"],
            "Contracts": o["contracts"],
            "P/L($)": round(pnl_d,2),
            "P/L(%)": round(pnl_p,2) if pnl_p is not None else None,
            "IV": (q.get("greeks",{}) or {}).get("iv")
        })

    # Save outputs (even if partial)
    pd.DataFrame(overlay_rows).sort_values("Ticker").to_csv(CONFIG["out_overlay_csv"], index=False)
    pd.DataFrame(pl_rows).to_csv(CONFIG["out_pl_csv"], index=False)
    pd.DataFrame(gap_rows).sort_values("Gap%").to_csv(CONFIG["out_gap_csv"], index=False)

    print("\n=== OVERLAY (VWAP / MACD / RSI) ===")
    try: print(pd.read_csv(CONFIG["out_overlay_csv"]).to_string(index=False))
    except Exception: print("(overlay not available)")

    print("\n=== ACTUAL OPTION P/L (mid used) ===")
    try: print(pd.read_csv(CONFIG["out_pl_csv"]).to_string(index=False))
    except Exception: print("(option P/L not available)")

    print("\n=== GAP DOWN ≥ -1% & ABOVE 100-SMA ===")
    try: print(pd.read_csv(CONFIG["out_gap_csv"]).to_string(index=False))
    except Exception: print("(gap screen not available)")

if __name__ == "__main__":
    main()
