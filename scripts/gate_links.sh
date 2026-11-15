#!/usr/bin/env bash
# Run hourly by cron. main.py decides (LINKS_POST_DAYS / LINKS_POST_HOUR in .env); it posts once per channel per day.
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
out=$(DRY_RUN=0 .venv/bin/python main.py --links-post --if-due 2>&1)
[ -n "$out" ] && { echo "=== $(date -Is)"; echo "$out"; } >> logs/links.log
exit 0
