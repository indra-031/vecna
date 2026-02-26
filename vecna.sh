#!/usr/bin/env bash

set -euo pipefail

DOMAINS_FILE="${1:-}"

if [[ -z "$DOMAINS_FILE" ]]; then
    echo "Usage: bash vecna.sh domains.txt"
    exit 1
fi

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOGS_DIR="$ROOT_DIR/logs"

mkdir -p "$LOGS_DIR"

# ----------------------------------
# Generate Run ID
# ----------------------------------

RUN_ID=1
while [[ -d "$LOGS_DIR/$RUN_ID" ]]; do
    RUN_ID=$((RUN_ID + 1))
done

ARCHIVE_DIR="$LOGS_DIR/$RUN_ID"
mkdir -p "$ARCHIVE_DIR"

LOG_FILE="$ARCHIVE_DIR/log.txt"

# 🔥 Real-time log
exec > >(stdbuf -oL tee -a "$LOG_FILE") 2>&1

# ----------------------------------
# Banner
# ----------------------------------

echo "======================================"
echo "               V E C N A   "
echo "======================================"
echo

# ----------------------------------
# Ensure working directories
# ----------------------------------

mkdir -p "$ROOT_DIR/output" "$ROOT_DIR/found" "$ROOT_DIR/poc"

# ----------------------------------
# Pipeline 
# ----------------------------------

echo "[1/12] DNS Intelligence..."
python3 -u "$ROOT_DIR/utils/dns-check.py" "$DOMAINS_FILE"
echo

echo "[2/12] HTTP Fingerprinting..."
python3 -u "$ROOT_DIR/utils/http-check.py"
echo

echo "[3/12] Internal Signature Matching..."
python3 -u "$ROOT_DIR/modules/matcher.py" "$DOMAINS_FILE"
echo

echo "[4/12] Can-I-Take-Over-Xyz Fingerprint Matching..."
python3 -u "$ROOT_DIR/3rd/can-i-take-over-xyz/can-i-take-over-xyz.py" "$DOMAINS_FILE"
echo

echo
echo "[5/12] SubJack Fingerprint Matching..."
python3 -u "$ROOT_DIR/3rd/subjack/subjack.py" "$DOMAINS_FILE"
echo

echo
echo "[6/12] SubOver Fingerprint Matching..."
python3 -u "$ROOT_DIR/3rd/subover/subover.py" "$DOMAINS_FILE"
echo

echo
echo "[7/12] Tko-Subs Fingerprint Matching..."
python3 -u "$ROOT_DIR/3rd/tko-subs/tko-subs.py" "$DOMAINS_FILE"
echo

echo
echo "[8/12] Nuclei Takeover Scan..."
python3 -u "$ROOT_DIR/modules/extract-alive.py"
python3 -u "$ROOT_DIR/3rd/nuclei/nuclei.py"
echo

echo
echo "[9/12] Merges Founds"
python3 -u "$ROOT_DIR/modules/report.py"
echo

echo "[10/12] Evidence Collection..."
python3 -u "$ROOT_DIR/modules/evidence_collector.py"
echo

echo "[11/12] Sending Telegram Alerts..."
python3 -u "$ROOT_DIR/telegram/notifier.py"
echo

echo "[12/12] Archiving & Cleanup..."
bash "$ROOT_DIR/logs/cleanup.sh" "$RUN_ID"
echo

echo "======================================"
echo "[✓] Vecna scan completed successfully."
echo "======================================"
