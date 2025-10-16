#!/usr/bin/env bash
# fetch.sh — resilient fetcher with layered fallbacks & backoff
# Usage: tools/fetch.sh <remote_path> <local_out> [<remote_path> <local_out> ...]

set -euo pipefail

OWNER="${OWNER:-Sevenon7}"
REPO="${REPO:-Sevenon7/Tradier_Options}"
BRANCH="${BRANCH:-main}"
TOKEN="${GITHUB_TOKEN:-${TOKEN:-}}"

ua="leaps-unified-fetcher/1.0 (+github actions)"
auth_hdr=()
[[ -n "$TOKEN" ]] && auth_hdr=(-H "Authorization: Bearer ${TOKEN}")

curl_get() {
  # $1=url  $2=outfile
  local url="$1" out="$2"
  local attempt=1 max=4
  while :; do
    set +e
    http=$(curl -sS -L -w "%{http_code}" -o "${out}.part" \
      -H "User-Agent: ${ua}" \
      -H "Accept: */*" \
      "${auth_hdr[@]}" \
      "$url")
    rc=$?
    set -e
    if [[ $rc -eq 0 && "$http" =~ ^2 ]]; then
      mv "${out}.part" "$out"
      return 0
    fi
    rm -f "${out}.part" || true
    if (( attempt >= max )); then
      return 22
    fi
    sleep $(( 2 ** attempt ))
    attempt=$(( attempt + 1 ))
  done
}

fetch_one() {
  local path="$1" out="$2"

  # 0) local file present?
  if [[ -f "$path" ]]; then
    cp -f "$path" "$out" && return 0
  fi

  # Base URLs
  local pages="https://${OWNER}.github.io/${REPO#*/}/${path}"
  local jsd="https://cdn.jsdelivr.net/gh/${REPO}@${BRANCH}/${path}"
  local raw="https://raw.githubusercontent.com/${REPO}/${BRANCH}/${path}"
  local api="https://api.github.com/repos/${REPO}/contents/${path}?ref=${BRANCH}"

  # 1) Pages
  if curl_get "$pages" "$out"; then return 0; fi
  echo "MISS (pages): $path" 1>&2

  # 2) jsDelivr
  if curl_get "$jsd" "$out"; then return 0; fi
  echo "MISS (jsDelivr): $path" 1>&2

  # 3) raw
  if curl_get "$raw" "$out"; then return 0; fi
  echo "MISS (raw): $path" 1>&2

  # 4) API (base64 decode)
  tmp="$(mktemp)"
  if curl_get "$api" "$tmp"; then
    if command -v jq >/dev/null 2>&1; then
      jq -r '.content' "$tmp" | tr -d '\n' | base64 --decode > "$out" || true
      rm -f "$tmp"
      [[ -s "$out" ]] && return 0
    fi
    rm -f "$tmp"
  fi

  echo "::error ::fetch failed for ${path} (all fallbacks exhausted)"
  return 22
}

# ---- main ----
if (( $# < 2 || ($# % 2) != 0 )); then
  echo "Usage: $0 <remote_path> <local_out> [<remote_path> <local_out> ...]" 1>&2
  exit 64
fi

while (( $# )); do
  rp="$1"; shift
  out="$1"; shift
  fetch_one "$rp" "$out"
done
