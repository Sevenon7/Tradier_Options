#!/usr/bin/env python3
"""
Consumer helper: read latest.json pointer, verify freshness (<=24h),
retry raw fetches for CSVs, and emit analysis_digest.json + .md
with overlay, option P/L, and gap screen tables.
"""

from __future__ import annotations
import os, sys, json, time
import datetime as dt
from typing import Optional, Tuple, List, Dict
import requests
import pandas as pd

REPO = os.environ.get("REPO", "Sevenon7/Tradier_Options")
BASE_RAW = f"https://raw.githubusercontent.com/{REPO}/main"
POINTER_URL = f"{BASE_RAW}/latest.json"

MAX_AGE_HOURS = int(os.environ.get("MAX_AGE_HOURS", "24"))
RETRY_COUNT = int(os.environ.get("RETRY_COUNT", "3"))
RETRY_SLEEP = float(os.environ.get("RETRY_SLEEP", "1.2"))

OUT_JSON = "analysis_digest.json"
OUT_MD   = "analysis_digest.md"

def fetch(url: str) -> Optional[str]:
    last_err = None
    for i in range(RETRY_COUNT):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200 and r.text:
                return r.text
            last_err = f"{r.status_code} {r.text[:200]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(RETRY_SLEEP * (i + 1))
    print(f"[warn] fetch failed for {url}: {last_err}")
    return None

def parse_json(text: str) -> Optional[dict]:
    try: return json.loads(text)
    except Exception: return None

def within_24h(ts_iso: str) -> bool:
    try:
        ts = dt.datetime.fromisoformat(ts_iso.replace("Z","+00:00"))
        age = dt.datetime.now(dt.timezone.utc) - ts
        return age.total_seconds() <= MAX_AGE_HOURS * 3600
    except Exception:
        return False

def build_raw(date_dir: str):
    overlay = f"{BASE_RAW}/{date_dir}/overlay_vwap_macd_rsi.csv"
    opl     = f"{BASE_RAW}/{date_dir}/option_pl.csv"
    gap     = f"{BASE_RAW}/{date_dir}/gapdown_above_100sma.csv"
    ready   = f"{BASE_RAW}/{date_dir}/READY"
    return overlay, opl, gap, ready

def csv_to_records(url: str) -> List[Dict]:
    txt = fetch(url)
    if not txt: return []
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(txt))
        df = df.where(pd.notna(df), None)
        return json.loads(df.to_json(orient="records"))
    except Exception as e:
        print(f"[warn] failed reading CSV {url}: {e}")
        return []

def main():
    summary = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "raw_links": {}, "overlay": [], "option_pl": [], "gap_screen": [], "notes": []
    }

    # Pointer first
    ptr = parse_json(fetch(POINTER_URL) or "") or {}
    date_dir = ptr.get("date_dir")
    if date_dir:
        fresh = within_24h(ptr.get("generated_utc",""))
        summary["notes"].append(f"Pointer freshness <=24h: {fresh}")
        if not fresh:
            summary["notes"].append("WARNING: latest.json older than 24h.")
    else:
        # Fallback: today UTC then yesterday
        now = dt.datetime.now(dt.timezone.utc)
        for d in [now, now - dt.timedelta(days=1)]:
            candidate = f"data/{d.strftime('%Y-%m-%d')}"
            if fetch(f"{BASE_RAW}/{candidate}/overlay_vwap_macd_rsi.csv"):
                date_dir = candidate
                summary["notes"].append(f"Fallback date_dir used: {date_dir}")
                break

    if not date_dir:
        summary["notes"].append("ERROR: No valid date_dir found.")
        with open(OUT_JSON, "w") as f: json.dump(summary, f, indent=2)
        with open(OUT_MD, "w") as f: f.write("# Analysis Digest (empty)\nNo valid data_dir found.\n")
        sys.exit(0)

    overlay_url, opl_url, gap_url, ready_url = build_raw(date_dir)
    summary["raw_links"] = {"overlay": overlay_url, "option_pl": opl_url, "gap_screen": gap_url, "ready": ready_url, "latest": POINTER_URL}

    ready_ok = fetch(ready_url) is not None
    summary["notes"].append(f"READY flag present: {ready_ok}")

    summary["overlay"] = csv_to_records(overlay_url)
    summary["option_pl"] = csv_to_records(opl_url)
    summary["gap_screen"] = csv_to_records(gap_url)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    def md_table(records, cols, title):
        if not records:
            return f"## {title}\n_No data_\n"
        s = [f"## {title}", "| " + " | ".join(cols) + " |", "| " + " | ".join(["---"]*len(cols)) + " |"]
        for r in records:
            s.append("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")
        return "\n".join(s) + "\n"

    overlay_cols = ["Ticker","RSI14","MACD>Signal","VWAP","LastPx","Px_vs_VWAP","SMA100","Gap%","Guidance"]
    pl_cols      = ["Contract","OCC","Bid","Ask","Last","MidUsed","Entry","Contracts","P/L($)","P/L(%)","IV","source","quote_status","spot_status","spot","strike","type","root","expiry","note"]
    gap_cols     = ["Ticker","Gap%","Close","SMA100"]

    md = []
    md.append(f"# Analysis Digest\n\n**date_dir:** `{date_dir}`  \n**generated_utc:** {summary['generated_utc']}  \n**latest.json:** {POINTER_URL}\n")
    md.append("### Raw links\n")
    md.append(f"- overlay: {overlay_url}\n- option_pl: {opl_url}\n- gap_screen: {gap_url}\n- ready: {ready_url}\n")
    md.append(md_table(summary["overlay"], overlay_cols, "Overlay (VWAP/MACD/RSI)"))
    md.append(md_table(summary["option_pl"], pl_cols, "Actual Option P/L"))
    md.append(md_table(summary["gap_screen"], gap_cols, "Gap Down ≥ -1% & Above 100-SMA"))
    if summary["notes"]:
        md.append("### Notes\n- " + "\n- ".join(summary["notes"]) + "\n")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

if __name__ == "__main__":
    main()
