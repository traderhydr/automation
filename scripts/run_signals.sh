#!/usr/bin/env bash
# Run every 5 minutes by cron: posts the 2 random free-sample signals per day (all logic/de-dupe is in the Python code).
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
flock -n logs/.signals.lock env DRY_RUN=0 .venv/bin/python main.py --signals --hours 4 >> logs/signals.log 2>&1
