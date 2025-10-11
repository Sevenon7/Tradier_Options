#!/usr/bin/env bash
set -euo pipefail

owner="${OWNER:-Sevenon7}"
repo="${REPO_NAME:-Tradier_Options}"
branch="${BRANCH:-main}"
site="https://${owner}.github.io/${repo}"

fetch_one() {
  src="$1"; dest="$2"
  mkdir -p "$(dirname "$dest")"

  # 1) local file in the checked-out workspace
  if [ -f "$src" ]; then
    cp -f "$src" "$dest"
    echo "hit:local $src -> $dest"
    return 0
  fi

  # 2) raw (public)
  raw="https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${src}"
  if curl -fsSL "$raw" -o "$dest" 2>/dev/null; then
    echo "hit:raw $src -> $dest"
    return 0
  else
    echo "MISS raw:$src"
  fi

  # 3) API (private-safe, raw bytes)
  api="https://api.github.com/repos/${owner}/${repo}/contents/${src}?ref=${branch}"
  if curl -fsSL -H "Authorization: Bearer ${GITHUB_TOKEN:-}" \
               -H "Accept: application/vnd.github.raw" \
               "$api" -o "$dest" 2>/dev/null; then
    echo "hit:api $src -> $dest"
    return 0
  else
    echo "MISS api:$src"
  fi

  # 4) gh-pages static mirror
  pages="${site}/${src}"
  if curl -fsSL "$pages" -o "$dest" 2>/dev/null; then
    echo "hit:pages $src -> $dest"
    return 0
  else
    echo "MISS pages:$src"
  fi

  return 1
}

# Pairs: SRC DEST SRC DEST ...
while [ "$#" -gt 0 ]; do
  s="$1"; d="$2"; shift 2 || true
  if ! fetch_one "$s" "$d"; then
    echo "ERR: fetch failed for $s" >&2
    exit 22
  fi
done
