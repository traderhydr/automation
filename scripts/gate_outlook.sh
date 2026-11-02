#!/usr/bin/env bash
# Run hourly by cron. Posts the BTC bounce-vs-dump chart once a day at 10:xx local time.
cd "$(dirname "$0")/.." || exit 1
TZN=$(grep -E '^TIMEZONE=' .env 2>/dev/null | head -1 | cut -d= -f2 | awk '{print $1}'); export TZ="${TZN:-Asia/Karachi}"
mkdir -p logs
[ "$(date +%H)" = "10" ] || exit 0
stamp="logs/.outlook_$(date +%F)"; [ -e "$stamp" ] && exit 0; touch "$stamp"
SYMS=$(grep -E '^OUTLOOK_SYMBOLS=' .env 2>/dev/null | head -1 | cut -d= -f2 | awk '{print $1}')
echo "=== $(date -Is) outlook ${SYMS:-BTCUSDT}" >> logs/outlook.log
DRY_RUN=0 .venv/bin/python main.py --scenario "${SYMS:-BTCUSDT}" >> logs/outlook.log 2>&1
