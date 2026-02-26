#!/usr/bin/env bash

set -euo pipefail

RUN_ID="${1:-}"

if [[ -z "$RUN_ID" ]]; then
    echo "Usage: cleanup.sh RUN_ID"
    exit 1
fi

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
ARCHIVE_DIR="$ROOT_DIR/logs/$RUN_ID"

FOUND_DIR="$ROOT_DIR/found"
OUTPUT_DIR="$ROOT_DIR/output"
POC_DIR="$ROOT_DIR/poc"

echo "[*] Moving files to logs/$RUN_ID ..."

[[ -d "$FOUND_DIR"  ]] && mv "$FOUND_DIR"  "$ARCHIVE_DIR/"
[[ -d "$OUTPUT_DIR" ]] && mv "$OUTPUT_DIR" "$ARCHIVE_DIR/"
[[ -d "$POC_DIR"    ]] && mv "$POC_DIR"    "$ARCHIVE_DIR/"

echo "[✓] Archive completed."