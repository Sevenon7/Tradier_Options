#!/usr/bin/env python3
import json, sys

def main():
    path = "vwap_missing.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception as e:
        print(f"::notice::VWAP warn helper could not read {path}: {e}")
        return 0

    for r in j.get("tickers", []):
        t = r.get("Ticker", "?")
        note = r.get("Note", "VWAP missing")
        # Emit a GitHub Actions warning per ticker
        print(f"::warning title=VWAP Missing::{t}: {note}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
