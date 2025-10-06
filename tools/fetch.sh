#!/usr/bin/env bash
# .github/tools/fetch.sh
# Robust fetcher: raw.githubusercontent.com  → GitHub REST API (raw) → GitHub Pages mirror
# Env you can set: REPO (owner/name), BRANCH, OWNER (for Pages), GITHUB_TOKEN
# Usage: fetch.sh <repo-path> <outfile> [<repo-path> <outfile> ...]

set -euo pipefail

REPO="${REPO:-Sevenon7/Tradier_Options}"
BRANCH="${BRANCH:-main}"
OWNER="${OWNER:-Sevenon7}"  # used for Pages fallback
AUTH="${GITHUB_TOKEN:-${GH_TOKEN:-}}"

is_html() {
  # quick heuristic
  grep -qiE '<(html|!doctype|title|meta)' "$1" 2>/dev/null
}

fetch_one() {
  local path="$1" out="$2" used=""

  local raw="https://raw.githubusercontent.com/${REPO}/${BRANCH}/${path}"
  local api="https://api.github.com/repos/${REPO}/contents/${path}?ref=${BRANCH}"
  local pages="https://${OWNER}.github.io/$(basename "${REPO}")/${path}"

  # --- 1) RAW CDN (fast) ---
  for attempt in 1 2 3; do
    if curl -fsSL --retry 2 --retry-delay 2 --max-time 25 "$raw" -o "$out"; then
      used="raw"
      break
    fi
    sleep $((attempt*2))
  done

  # --- 2) REST API (raw) ---
  if [ -z "${used}" ] || [ ! -s "$out" ] || is_html "$out"; then
    rm -f "$out"
    if curl -fsSL --max-time 25 \
      -H "Accept: application/vnd.github.raw" \
      ${AUTH:+-H "Authorization: Bearer ${AUTH}"} \
      "$api" -o "$out" ; then
      used="api"
    fi
  fi

  # --- 3) GitHub Pages mirror ---
  if [ -z "${used}" ] || [ ! -s "$out" ] || is_html "$out"; then
    rm -f "$out"
    if curl -fsSL --max-time 25 "$pages" -o "$out" ; then
      used="pages"
    fi
  fi

  # --- Validate result ---
  if [ ! -s "$out" ] || is_html "$out"; then
    echo "::error ::fetch.sh failed for ${path} (raw/api/pages)"
    return 1
  fi

  echo "fetched:${path} method:${used} size:$(wc -c < "$out")" >&2
}

while (( "$#" )); do
  p="$1"; o="$2"; shift 2
  fetch_one "$p" "$o"
done
