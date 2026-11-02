#!/usr/bin/env bash
# Run hourly by cron. Does work only between 00:00 and 02:59 local time (TIMEZONE in .env), so a missed run catches up.
#   every day -> daily report for yesterday;  Monday -> + weekly (Mon-Sun week that ended);  1st -> + monthly;  1 Jan -> + yearly
cd "$(dirname "$0")/.." || exit 1
TZN=$(grep -E '^TIMEZONE=' .env 2>/dev/null | head -1 | cut -d= -f2 | awk '{print $1}'); export TZ="${TZN:-Asia/Karachi}"
mkdir -p logs
case "$(date +%H)" in 00|01|02) ;; *) exit 0 ;; esac
y=$(date -d yesterday +%F); jobs="daily:$y"
[ "$(date -d yesterday +%u)" = "7" ] && jobs="$jobs weekly:$y"
[ "$(date +%d)" = "01" ]             && jobs="$jobs monthly:$y"
[ "$(date +%m-%d)" = "01-01" ]       && jobs="$jobs yearly:$y"
for j in $jobs; do
  echo "=== $(date -Is) $j" >> logs/reports.log
  DRY_RUN=0 .venv/bin/python main.py --period "${j%%:*}" --date "${j##*:}" >> logs/reports.log 2>&1
done
