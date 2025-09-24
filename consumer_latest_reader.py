#!/usr/bin/env python3
"""
Consumer helper: read latest.json pointer, verify freshness (<=24h),
retry raw fetches for CSVs, and emit a single analysis_digest.json + .md
with overlay, option P/L, and gap screen tables.

This does NOT compute new signals; it consolidates the repo outputs so
downstream tools (like your ChatGPT automation) can read one file.
"""

from __future__ import annotations
import os, sys, json, time, math
import datetime as dt
from typing import Optional, Tuple
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

def fetch(url: str, expect_json=False) -> Optional[str]:
    """GET with small retry/backoff; returns text or None."""
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
    try:
        return json.loads(text)
    except Exception:
        return None

def iso_now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def within_24h(ts_iso: str) -> bool:
    try:
        ts = dt.datetime.fromisoformat(ts_iso.replace("Z","+00:00"))
        age = dt.datetime.now(dt.timezone.utc) - ts
        return age.total_seconds() <= MAX_AGE_HOURS * 3600
    except Exception:
        return False

def build_raw(date_dir: str) -> Tuple[str, str, str, str]:
    overlay = f"{BASE_RAW}/{date_dir}/overlay_vwap_macd_rsi.csv"
    opl     = f"{BASE_RAW}/{date_dir}/option_pl.csv"
    gap     = f"{BASE_RAW}/{date_dir}/gapdown_above_100sma.csv"
    ready   = f"{BASE_RAW}/{date_dir}/READY"
    return overlay, opl, gap, ready

def csv_to_records(url: str) -> list[dict]:
    txt = fetch(url)
    if not txt:
        return []
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(txt))
        # sanitize NaN/inf to None for JSON
        df = df.where(pd.notna(df), None)
        return json.loads(df.to_json(orient="records"))
    except Exception as e:
        print(f"[warn] failed reading CSV {url}: {e}")
        return []

def main():
    summary = {
        "generated_by": "consumer_latest_reader.py",
        "generated_utc": iso_now_utc(),
        "raw_links": {},
        "overlay": [],
        "option_pl": [],
        "gap_screen": [],
        "notes": []
    }

    # 1) Try latest.json pointer first
    ptr_text = fetch(POINTER_URL)
    if ptr_text:
        ptr = parse_json(ptr_text)
    else:
        ptr = None

    date_dir = None
    if ptr and isinstance(ptr, dict) and "date_dir" in ptr:
        date_dir = ptr["date_dir"]
        summary["notes"].append("Pointer latest.json found.")
        if "generated_utc" in ptr:
            fresh = within_24h(ptr["generated_utc"])
            summary["notes"].append(f"Pointer freshness: {ptr['generated_utc']} (<=24h={fresh})")
            if not fresh:
                summary["notes"].append("WARNING: latest.json older than 24h.")
    else:
        summary["notes"].append("Pointer latest.json missing or invalid; falling back to date guess.")
        # Fallback: try today UTC then yesterday
        now = dt.datetime.now(dt.timezone.utc)
        for d in [now, now - dt.timedelta(days=1)]:
            candidate = f"data/{d.strftime('%Y-%m-%d')}"
            # Try overlay existence
            overlay_url, opl_url, gap_url, ready_url = build_raw(candidate)
            if fetch(overlay_url):  # file exists
                date_dir = candidate
                summary["notes"].append(f"Using fallback date_dir={date_dir}")
                break

    if not date_dir:
        summary["notes"].append("ERROR: No valid date_dir found (pointer/fallback failed).")
        print(json.dumps(summary, indent=2))
        # still write out empty digest
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        with open(OUT_MD, "w", encoding="utf-8") as f:
            f.write("# Analysis Digest (empty)\nNo valid data_dir found.\n")
        sys.exit(0)

    overlay_url, opl_url, gap_url, ready_url = build_raw(date_dir)
    summary["raw_links"] = {"overlay": overlay_url, "option_pl": opl_url, "gap_screen": gap_url, "ready": ready_url, "latest": POINTER_URL}

    # Check READY flag (optional)
    ready_ok = fetch(ready_url) is not None
    summary["notes"].append(f"READY flag present: {ready_ok}")

    # 2) Load CSVs
    summary["overlay"] = csv_to_records(overlay_url)
    summary["option_pl"] = csv_to_records(opl_url)
    summary["gap_screen"] = csv_to_records(gap_url)

    # 3) Emit JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 4) Emit Markdown summary (compact tables)
    def md_table(records: list[dict], cols: list[str], title: str) -> str:
        if not records:
            return f"## {title}\n_No data_\n"
        # header
        s = [f"## {title}", "| " + " | ".join(cols) + " |", "| " + " | ".join(["---"]*len(cols)) + " |"]
        for r in records:
            s.append("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")
        return "\n".join(s) + "\n"

    overlay_cols = ["Ticker","RSI14","MACD>Signal","VWAP","LastPx","Px_vs_VWAP","SMA100","Gap%","Guidance"]
    pl_cols      = ["Contract","OCC","Bid","Ask","Last","MidUsed","Entry","Contracts","P/L($)","P/L(%)","IV"]
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

    print(json.dumps({"status":"ok","date_dir":date_dir,"ready":ready_ok}, indent=2))

if __name__ == "__main__":
    main()
