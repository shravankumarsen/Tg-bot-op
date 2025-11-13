#!/usr/bin/env bash
set -e

# Ensure aria2 is installed (Koyeb buildpacks provide it only sometimes)
# If not installed, we skip — Dockerfile users always have aria2.

# Start aria2 in background
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

# Run your bot
exec python3 terabox.py
