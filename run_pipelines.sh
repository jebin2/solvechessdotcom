#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REELFORGE_DIR="$SCRIPT_DIR"

while true; do
    echo "[$(date)] Running solvechessdotcom..."
    cd "$REELFORGE_DIR" && bash run_app.sh --onepass

    echo "[$(date)] Sleeping for 60 seconds..."
    sleep 60
done
