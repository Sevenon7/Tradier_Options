#!/usr/bin/env bash
# tools/fetch.sh
# Usage:
#   tools/fetch.sh <src1> <dest1> [<src2> <dest2> ...]
# Where <src> is a repo-relative path (e.g., data/2025-10-02/overlay_vwap_macd_rsi.csv)
# and <dest> is a local file path to write.

set -euo pipefail

# ---- Config discovery ---------------------------------------------------------
OWNER_DEFAULT="${OWNER:-}"
REPO_DEFAULT="${REPO:-}"
BRANCH_DEFAULT="${BRANCH:-main}"

# Try to infer OWNER/REPO from git remote if not provided
if [[ -z "${OWNER_DEFAULT}" || -z "${REPO_DEFAULT}" ]]; then
  remote_url="$(git config --get remote.origin.url || true)"
  if [[ -n "$remote_url" ]]; then
    # Handle https and ssh formats
    # https://github.com/Owner/Repo.git
    # git@github.com:Owner/Repo.git
    repo_path="${remote_url%.git}"
    repo_path="${repo_path#git@github.com:}"
    repo_path="${repo_path#https://github.com/}"
    OWNER_DEFAULT="${repo_path%%/*}"
    REPO_DEFAULT="${repo_path##*/}"
  fi
fi

OWNER="${OWNER_DEFAULT:?OWNER env not set and could not infer from git remote}"
REPO="${REPO_DEFAULT:?REPO env not set and could not infer from git remote}"
BRANCH="${BRANCH_DEFAULT}"

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
PAGES_BASE="${PAGES_BASE:-https://${OWNER}.github.io/${REPO}}"

debug() { [[ "${FETCH_DEBUG:-false}" == "true" ]] && echo "[fetch.sh] $*" >&2 || true; }

curl_raw() {
  local src="$1" dest="$2"
  local url="https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}/${src}"
  debug "RAW   → ${url}"
  if curl -fL --retry 3 --retry-delay 2 -sS "${url}" -o "${dest}"; then
    echo "raw" > "${dest}.source"
    return 0
  fi
  return 1
}

curl_api_contents() {
  local src="$1" dest="$2"
  local url="https://api.github.com/repos/${OWNER}/${REPO}/contents/${src}?ref=${BRANCH}"
  debug "API   → ${url}"
  # Use the contents API with "raw" accept to stream file bytes directly.
  # Docs: REST API → Repository contents. Accept: application/vnd.github.raw
  # https://docs.github.com/en/rest/repos/contents
  local auth=()
  [[ -n "${GITHUB_TOKEN}" ]] && auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  if curl -fSL -sS \
      -H "Accept: application/vnd.github.raw" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "${auth[@]}" \
      "${url}" -o "${dest}"; then
    echo "api" > "${dest}.source"
    return 0
  fi
  return 1
}

curl_pages() {
  local src="$1" dest="$2"
  local url="${PAGES_BASE}/${src}"
  debug "PAGES → ${url}"
  if curl -fL --retry 3 --retry-delay 2 -sS "${url}" -o "${dest}"; then
    echo "pages" > "${dest}.source"
    return 0
  fi
  return 1
}

fetch_one() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  rm -f "${dest}" "${dest}.source"

  # Try RAW → API → PAGES
  if curl_raw        "$src" "$dest"; then echo "OK: ${src} (raw)   → ${dest}"; return 0; fi
  if curl_api_contents "$src" "$dest"; then echo "OK: ${src} (api)   → ${dest}"; return 0; fi
  if curl_pages      "$src" "$dest"; then echo "OK: ${src} (pages) → ${dest}"; return 0; fi

  echo "MISS: ${src}" >&2
  return 1
}

if (( $# == 0 || ($# % 2) != 0 )); then
  echo "Usage: $0 <src1> <dest1> [<src2> <dest2> ...]" >&2
  exit 64
fi

overall_ok=true
while (( "$#" )); do
  src="$1"; dest="$2"; shift 2
  if ! fetch_one "$src" "$dest"; then
    overall_ok=false
  fi
done

$overall_ok && exit 0 || exit 1
