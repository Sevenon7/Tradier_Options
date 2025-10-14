#!/usr/bin/env bash
# Usage:
#   tools/fetch.sh SRC1 DST1 [SRC2 DST2 ...]
# Where SRC is a path relative to repo root, e.g. "data/2025-10-10/overlay_vwap_macd_rsi.csv"
# Dest is a local filepath to write.

set -euo pipefail

OWNER="${OWNER:-Sevenon7}"
REPO="${REPO:-Tradier_Options}"
BRANCH="${BRANCH:-main}"

PAGES_BASE="${PAGES_BASE:-https://${OWNER}.github.io/${REPO}}"
JSDELIVR_BASE="${JSDELIVR_BASE:-https://cdn.jsdelivr.net/gh/${OWNER}/${REPO}@${BRANCH}}"
RAW_BASE="${RAW_BASE:-https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}}"

UA="${UA:-Sevenon7-LEAPS/1.0 (curl)}"
ACCEPT="${ACCEPT:-text/plain, application/octet-stream, */*}"
MAX_RETRIES="${MAX_RETRIES:-4}"
SLEEP_BASE="${SLEEP_BASE:-2}" # seconds

log() { echo "[$(date -u +%H:%M:%S)] $*" >&2; }

curl_get() {
  # $1 URL, $2 OUT
  local url="$1" out="$2"
  local code
  code=$(curl -fsSL -A "$UA" -H "Accept: $ACCEPT" -w "%{http_code}" -o "$out" "$url" || true)
  echo "$code"
}

fetch_one() {
  # $1 SRC path, $2 DEST
  local src="$1" dest="$2"
  local tries=0
  local urls=(
    "${PAGES_BASE}/${src}"
    "${JSDELIVR_BASE}/${src}"
    "${RAW_BASE}/${src}"
  )

  mkdir -p "$(dirname "$dest")"

  for (( tries=1; tries<=MAX_RETRIES; tries++ )); do
    local u
    for u in "${urls[@]}"; do
      log "GET (try ${tries}/${MAX_RETRIES}) → ${u}"
      code=$(curl_get "$u" "$dest")
      if [[ "$code" == "200" ]]; then
        log "OK ${u} → ${dest}"
        return 0
      fi
      # treat 404 on first two mirrors as soft-fail; 429/5xx backoff
      if [[ "$code" =~ ^(429|5..) ]]; then
        sleep_time=$(( SLEEP_BASE * tries ))
        log "HTTP $code from ${u} — backing off ${sleep_time}s"
        sleep "${sleep_time}"
        continue
      fi
      log "HTTP $code from ${u}"
    done
    # between rounds wait a bit
    sleep_time=$(( SLEEP_BASE * tries ))
    log "Round ${tries} done — sleeping ${sleep_time}s before retry"
    sleep "${sleep_time}"
  done

  log "FAILED to fetch ${src} after ${MAX_RETRIES} attempts"
  return 1
}

# Parse pairs
if (( "$#" % 2 != 0 )); then
  echo "Usage: $0 SRC1 DST1 [SRC2 DST2 ...]" >&2
  exit 2
fi

while (( "$#" )); do
  SRC="$1"; DST="$2"; shift 2
  fetch_one "$SRC" "$DST"
done
