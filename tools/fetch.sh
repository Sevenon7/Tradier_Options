#!/usr/bin/env bash
# tools/fetch.sh
# Fetch repo files with fallback chain: Pages → jsDelivr → raw → API(raw)
# Usage: fetch.sh <src1> <dest1> [<src2> <dest2> ...]
#   srcN  = path in repo (e.g., latest.json or data/YYYY-MM-DD/overlay_vwap_macd_rsi.csv)
#   destN = local path to write

set -euo pipefail

OWNER="${OWNER:-Sevenon7}"
REPO="${REPO:-Tradier_Options}"
BRANCH="${BRANCH:-main}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

UA="LEAPS-Automation/1.0 (+https://github.com/${OWNER}/${REPO})"

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }

usage() {
  cat >&2 <<USAGE
Usage: $0 <src1> <dest1> [<src2> <dest2> ...]
  srcN:  repo path (e.g., latest.json, data/YYYY-MM-DD/overlay_vwap_macd_rsi.csv)
  destN: local destination path
Env:
  OWNER=${OWNER}  REPO=${REPO}  BRANCH=${BRANCH}
  GITHUB_TOKEN: optional; used only for raw.githubusercontent.com and api.github.com
USAGE
  exit 2
}

# curl with backoff; set auth headers only for github domains
curl_dl() {
  local url="$1" dest="$2" max=3 attempt=1
  local tmp="${dest}.tmp"
  local extra=()

  case "$url" in
    https://raw.githubusercontent.com/*|https://api.github.com/*)
      [[ -n "$GITHUB_TOKEN" ]] && extra+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
      ;;
    https://*.github.io/*|https://cdn.jsdelivr.net/*)
      # never send tokens to these hosts
      :
      ;;
  esac

  while (( attempt <= max )); do
    log "GET ($attempt/$max): $url"
    if curl -fL --retry 0 --connect-timeout 10 --max-time 60 \
            -A "${UA}" "${extra[@]}" -o "${tmp}" "$url"; then
      # Accept only non-empty content
      if [[ -s "${tmp}" ]]; then
        # Guard against HTML "soft 200" pages
        if head -c 256 "${tmp}" | tr -d '\r' | grep -qiE '^<!doctype html|^<html|rate limit exceeded|not found|error'; then
          log "⚠️  Discarding HTML/error payload from ${url}"
          rm -f "${tmp}"
        else
          mv -f "${tmp}" "${dest}"
          return 0
        fi
      else
        log "⚠️  Empty body from ${url}"
        rm -f "${tmp}"
      fi
    else
      rc=$?
      log "⚠️  curl failed (rc=$rc) for ${url}"
      rm -f "${tmp}" || true
    fi

    # backoff: 1s, 3s, 5s
    sleep $(( (attempt-1)*2 + 1 ))
    attempt=$(( attempt + 1 ))
  done
  return 1
}

# Try each mirror in order for a single file
fetch_one() {
  local path="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"

  # Mirrors (order matters)
  local pages="https://${OWNER}.github.io/${REPO}/${path}"
  local jsdeliv="https://cdn.jsdelivr.net/gh/${OWNER}/${REPO}@${BRANCH}/${path}"
  local raw="https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}/${path}"
  local api="https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}?ref=${BRANCH}"

  # 1) GitHub Pages
  if curl_dl "${pages}" "${dest}"; then
    log "✅ ${dest} ← GitHub Pages"
    return 0
  fi

  # 2) jsDelivr
  if curl_dl "${jsdeliv}" "${dest}"; then
    log "✅ ${dest} ← jsDelivr"
    return 0
  fi

  # 3) raw.githubusercontent.com
  if curl_dl "${raw}" "${dest}"; then
    log "✅ ${dest} ← raw.githubusercontent.com"
    return 0
  fi

  # 4) GitHub API (raw)
  if [[ -n "$GITHUB_TOKEN" ]]; then
    log "GET (API raw): ${api}"
    if curl -fL -A "${UA}" \
          -H "Authorization: Bearer ${GITHUB_TOKEN}" \
          -H "Accept: application/vnd.github.raw" \
          -o "${dest}.tmp" "${api}" && [[ -s "${dest}.tmp" ]]; then
      mv -f "${dest}.tmp" "${dest}"
      log "✅ ${dest} ← api.github.com (raw)"
      return 0
    else
      rm -f "${dest}.tmp" || true
    fi
  else
    log "ℹ️  Skipping API fallback (no GITHUB_TOKEN set)"
  fi

  log "❌ Failed to fetch ${path}"
  return 1
}

# ---- Main ----
(( $# == 0 || ($# % 2) != 0 )) && usage

status=0
while (( $# )); do
  src="$1"; dst="$2"; shift 2
  if ! fetch_one "$src" "$dst"; then
    status=1
  fi
done
exit $status
