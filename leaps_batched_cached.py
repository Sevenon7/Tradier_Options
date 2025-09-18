#!/usr/bin/env python3
"""
LEAPS Overlay Runner (Batched + Cached for Tradier)
--------------------------------------------------
- Pulls/caches DAILY OHLCV for indicators (RSI14, MACD 12/26/9, SMA100, gap%)
- Pulls INTRADAY 5-min time-sales for session VWAP (per ticker)
- Batches equity quotes and options quotes (single call each)
- Computes "Actual option P/L" using mid = (bid+ask)/2 (fallback to last if one-sided)
- Emits 3 CSVs: overlay, option_pl, gap_screen

USAGE
-----
export TRADIER_TOKEN="YOUR_TOKEN"
python3 leaps_batched_cached.py

CONFIG
------
Edit the CONFIG dict below to change tickers/contracts.

SECURITY
--------
Do NOT hardcode your token. Use TRADIER_TOKEN env var.
"""

import os, sys, math, datetime as dt, requests, pandas as pd

BASE = "https://api.tradier.com/v1"
TOKEN = os.getenv("TRADIER_TOKEN")
if not TOKEN:
    print("ERROR: Set TRADIER_TOKEN environment variable.")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

# -------- CONFIG --------
CONFIG = {
    "tickers": ["QQQ","META","MSFT","MSTU","MSTR","PLTR","AMD","NVDA","BBAI","RKLB","VST","ASTS","RDDT","UUUU"],
    # OCC symbols + entry + contracts
    "open_options": [
        {"occ":"META260220C00700000","entry":109.13,"contracts":1,  "label":"META 700C Feb '26"},
        {"occ":"MSTU260320C00005000","entry":1.86,  "contracts":20, "label":"MSTU 5C Mar '26"},
    ],
    "cache_dir": "./tradier_cache",
    "daily_lookback_days": 400,
    "session_start": "09:30",
    "session_end":   None,
    "interval": "5min",
    "out_overlay_csv": "overlay_vwap_macd_rsi.csv",
    "out_pl_csv": "option_pl.csv",
    "out_gap_csv": "gapdown_above_100sma.csv",
}

# -------- Utility functions (RSI, MACD, VWAP, SMA, etc.) --------
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
    if df.empty: return math.nan, math.nan
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    vwap = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
    return float(vwap.iloc[-1]), float(df["close"].iloc[-1])

def mid_from_quote(q):
    bid, ask, last = map(lambda x: float(x or 0), (q.get("bid"), q.get("ask"), q.get("last")))
    return (bid+ask)/2 if bid and ask else last or bid or ask

# -------- API helpers --------
def get_daily_history(symbol, start, end):
    r = requests.get(f"{BASE}/markets/history",
        headers=HEADERS, params={"symbol":symbol,"interval":"daily","start":start,"end":end}, timeout=25)
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("history",{}).get("day",[]))
    if df.empty: return df
    df["date"]=pd.to_datetime(df["date"])
    for c in ["open","high","low","close","volume"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.sort_values("date")

def get_intraday_timesales(symbol, start, end, interval="5min"):
    r = requests.get(f"{BASE}/markets/timesales",
        headers=HEADERS,
        params={"symbol":symbol,"interval":interval,
                "start":start.strftime("%Y-%m-%d %H:%M"),
                "end":end.strftime("%Y-%m-%d %H:%M"),
                "session_filter":"all"},
        timeout=25)
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("series",{}).get("data",[]))
    if df.empty: return df
    df["time"]=pd.to_datetime(df["time"])
    for c in ["open","high","low","close","volume"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.sort_values("time")

def batch_equity_quotes(symbols):
    r = requests.get(f"{BASE}/markets/quotes",headers=HEADERS,params={"symbols":",".join(symbols)},timeout=20)
    r.raise_for_status()
    q = r.json().get("quotes",{}).get("quote",[])
    if isinstance(q,dict): q=[q]
    return {row["symbol"]:row for row in q}

def options_quotes(occs):
    r = requests.get(f"{BASE}/markets/options/quotes",headers=HEADERS,
        params={"symbols":",".join(occs),"greeks":"true"},timeout=20)
    r.raise_for_status()
    q = r.json().get("options",{}).get("quote",[])
    if isinstance(q,dict): q=[q]
    return {row["symbol"]:row for row in q}

# -------- Main --------
def main():
    today=dt.datetime.now()
    start_date=(today-dt.timedelta(days=CONFIG["daily_lookback_days"])).strftime("%Y-%m-%d")
    end_date=today.strftime("%Y-%m-%d")

    quotes=batch_equity_quotes(CONFIG["tickers"])
    daily_frames={sym:get_daily_history(sym,start_date,end_date) for sym in CONFIG["tickers"]}

    overlay_rows=[]; gap_rows=[]
    session_start=dt.datetime.combine(today.date(),dt.datetime.strptime(CONFIG["session_start"],"%H:%M").time())
    session_end=dt.datetime.now()

    for sym,ddf in daily_frames.items():
        if ddf.empty: continue
        ddf["SMA100"]=sma(ddf["close"],100)
        ddf["RSI14"]=rsi(ddf["close"],14)
        macd_line,sig_line,_=macd(ddf["close"],12,26,9)
        ddf["MACD"],ddf["MACDsig"]=macd_line,sig_line
        last,prev=ddf.iloc[-1],ddf.iloc[-2]
        gap_pct=(last["open"]-prev["close"])/prev["close"]*100

        try: idf=get_intraday_timesales(sym,session_start,session_end,CONFIG["interval"])
        except: idf=pd.DataFrame()
        vwap,last_px=session_vwap_from_bars(idf) if not idf.empty else (math.nan,quotes.get(sym,{}).get("last",math.nan))
        above_vwap=(float(last_px)>float(vwap)) if vwap==vwap else None
        macd_pos=bool(last["MACD"]>last["MACDsig"])
        rsi_val=float(last["RSI14"])

        if (above_vwap is False) and (not macd_pos) and (rsi_val<45): guidance="EXIT"
        elif (above_vwap is False) or (rsi_val>70 and not macd_pos): guidance="TRIM"
        else: guidance="HOLD"

        overlay_rows.append({"Ticker":sym,"RSI14":round(rsi_val,2),"MACD>Signal":macd_pos,
                             "VWAP":round(vwap,2),"LastPx":round(last_px,2),
                             "Px_vs_VWAP":"Above" if above_vwap else "Below",
                             "SMA100":round(last["SMA100"],2),"Gap%":round(gap_pct,2),"Guidance":guidance})
        if gap_pct<=-1.0 and last["close"]>last["SMA100"]:
            gap_rows.append({"Ticker":sym,"Gap%":round(gap_pct,2),"Close":last["close"],"SMA100":last["SMA100"]})

    oq=options_quotes([o["occ"] for o in CONFIG["open_options"]])
    pl_rows=[]
    for o in CONFIG["open_options"]:
        q=oq.get(o["occ"],{})
        mid=mid_from_quote(q)
        pnl_d=(mid-o["entry"])*100*o["contracts"]
        pnl_p=(mid/o["entry"]-1)*100 if o["entry"] else None
        pl_rows.append({"Contract":o["label"],"MidUsed":round(mid,2),"Entry":o["entry"],
                        "Contracts":o["contracts"],"P/L($)":round(pnl_d,2),"P/L(%)":round(pnl_p,2)})

    pd.DataFrame(overlay_rows).to_csv(CONFIG["out_overlay_csv"],index=False)
    pd.DataFrame(pl_rows).to_csv(CONFIG["out_pl_csv"],index=False)
    pd.DataFrame(gap_rows).to_csv(CONFIG["out_gap_csv"],index=False)

if __name__=="__main__": main()
