#!/usr/bin/env bash
# Send emails to contacts marked "To send" in the Google Sheet
# Usage:
#   bash run-send.sh              # send to all "To send" rows
#   bash run-send.sh --limit 10   # send to first 10 "To send" rows only

cd "$(dirname "$0")"

LIMIT=""
for arg in "$@"; do
    LIMIT="$LIMIT $arg"
done

gemini --yolo -p "/school-send${LIMIT}"
