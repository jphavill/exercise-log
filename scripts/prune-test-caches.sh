#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CACHE_TTL_DAYS="${1:-${CACHE_TTL_DAYS:-14}}"
CACHE_BASE_DIR="${CACHE_BASE_DIR:-$REPO_ROOT/.cache}"

if ! [[ "$CACHE_TTL_DAYS" =~ ^[0-9]+$ ]]; then
  printf 'CACHE_TTL_DAYS must be a non-negative integer, got: %s\n' "$CACHE_TTL_DAYS"
  exit 1
fi

npm_cache_dir="$CACHE_BASE_DIR/npm"
if [ -d "$npm_cache_dir" ]; then
  find "$npm_cache_dir" -mindepth 1 -mtime +"$CACHE_TTL_DAYS" -exec rm -rf {} +
fi

frontend_modules_cache_dir="$CACHE_BASE_DIR/frontend-node_modules"
if [ -d "$frontend_modules_cache_dir" ]; then
  find "$frontend_modules_cache_dir" -mindepth 1 -maxdepth 1 -type d -mtime +"$CACHE_TTL_DAYS" -exec rm -rf {} +
fi
