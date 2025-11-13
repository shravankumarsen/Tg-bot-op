#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# Start aria2 in background (installed by Dockerfile)
aria2c --enable-rpc \
       --rpc-listen-all=false \
       --rpc-allow-origin-all \
       --daemon=true \
       --max-tries=50 \
       --retry-wait=3 \
       --continue=true \
       --min-split-size=4M \
       --split=10 \
       --allow-overwrite=true || true

sleep 2

# Run the bot with exec (so container PID 1 is python)
exec python3 terabox.py
