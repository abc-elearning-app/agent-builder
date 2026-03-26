#!/usr/bin/env bash
# Run school contact discovery
# Usage:
#   bash run-discover.sh
#
# The agent will search for school websites across all US states,
# scrape contact pages for real emails, and write results to the Google Sheet.

cd "$(dirname "$0")"
gemini --yolo -p "/school-discover"
