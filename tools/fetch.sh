#!/usr/bin/env bash
set -euo pipefail

# Hardened fetcher with retries and multi-origin fallback:
# Order: GitHub Pages → jsDelivr → raw.githubusercontent.com
# Usage: fetch.sh <src1> <dest1> [<src2> <dest2> ...]

OWNER="${OWNER:-Sevenon7}"
REPO="${REPO:-Tradier_Options}"
BRANCH="${BRANCH:-main}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

PAGES_BASE="https://${OWNER}.github.io/${REPO}"
JSDELIVR_BASE="https://cdn.jsdelivr.net/gh/${OWNER}/${REPO}@${BRANCH}"
RAW_BASE="https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}"

hdr_auth=()
[[ -n "$GITHUB_TOKEN" ]] && hdr_auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}" -H "X-GitHub-Api-Version: 2022-11-28")

fetch_one() {
  local src="$1" dest="$2"
  local url pages_url jsd_url raw_url
  pages_url="${PAGES_BASE}/${src}"
  jsd_url="${JSDELIVR_BASE}/${src}"
  raw_url="${RAW_BASE}/${src}"

  local tries=( "$pages_url" "$jsd_url" "$raw_url" )
  local ok=0 http code=0

  for url in "${tries[@]}"; do
    for attempt in {1..4}; do
      # note: only pass auth headers to raw/github; pages/jsdelivr ignore safely
      if [[ "$url" == "$raw_url" ]]; then
        http=$(curl -sS -L -w '%{http_code}' -o "${dest}.tmp" "${hdr_auth[@]}" "$url" || echo "000")
      else
        http=$(curl -sS -L -w '%{http_code}' -o "${dest}.tmp" "$url" || echo "000")
      fi
      code="${http: -3}"
      if [[ "$code" == "200" ]]; then
        mv -f "${dest}.tmp" "$dest"; ok=1; break
      fi
      sleep $((attempt * 2))
    done
    [[ $ok -eq 1 ]] && break
  done

  if [[ $ok -ne 1 ]]; then
    echo "::error::Failed to fetch ${src} (last status ${code})"
    return 1
  fi
  return 0
}

[[ "$#" -ge 2 ]] || { echo "Usage: $0 <src1> <dest1> [<src2> <dest2> ...]"; exit 2; }
(( $# % 2 == 0 )) || { echo "::error::Arguments must be pairs <src> <dest>"; exit 2; }

while (( "$#" )); do
  s="$1"; d="$2"; shift 2
  fetch_one "$s" "$d" || exit 1
done

echo "✅ Fetch complete."
