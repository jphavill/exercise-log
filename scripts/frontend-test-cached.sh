#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

FRONTEND_DIR="$REPO_ROOT/frontend"
CACHE_ROOT="${CACHE_ROOT:-$REPO_ROOT/.cache/frontend-node_modules}"
NPM_CACHE_DIR="${NPM_CACHE_DIR:-$REPO_ROOT/.cache/npm}"
NODE_TEST_IMAGE="${NODE_TEST_IMAGE:-node:22-alpine}"

LOCKFILE="$FRONTEND_DIR/package-lock.json"
if [ ! -f "$LOCKFILE" ]; then
  printf 'Missing lockfile: %s\n' "$LOCKFILE"
  exit 1
fi

lock_hash="$(shasum -a 256 "$LOCKFILE" | awk '{print $1}')"
image_hash="$(printf '%s' "$NODE_TEST_IMAGE" | shasum -a 256 | awk '{print $1}')"
cache_key="$(printf '%s:%s' "$lock_hash" "$image_hash" | shasum -a 256 | awk '{print $1}')"

NODE_MODULES_CACHE_DIR="$CACHE_ROOT/$cache_key"
mkdir -p "$NODE_MODULES_CACHE_DIR" "$NPM_CACHE_DIR"

docker run --rm \
  -e CACHE_KEY="$cache_key" \
  -e NPM_CONFIG_CACHE=/npm-cache \
  -v "$FRONTEND_DIR:/app" \
  -v "$NODE_MODULES_CACHE_DIR:/app/node_modules" \
  -v "$NPM_CACHE_DIR:/npm-cache" \
  -w /app \
  "$NODE_TEST_IMAGE" \
  sh -euc '
    marker="node_modules/.cache-key"

    if [ ! -f "$marker" ] || [ "$(cat "$marker")" != "$CACHE_KEY" ]; then
      npm ci --prefer-offline
      printf "%s" "$CACHE_KEY" > "$marker"
    elif ! npm ls --depth=0 >/dev/null 2>&1; then
      npm ci --prefer-offline
      printf "%s" "$CACHE_KEY" > "$marker"
    fi

    npm test -- "$@"
  ' sh "$@"

touch "$NODE_MODULES_CACHE_DIR"
