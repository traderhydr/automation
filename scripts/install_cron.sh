#!/usr/bin/env bash
# Installs the schedule into your crontab (safe to re-run: it replaces its own block).
#   ./scripts/install_cron.sh                 -> BTC outlook + free signals + results reports
#   ./scripts/install_cron.sh --no-reports    -> without results reports
set -e
cd "$(dirname "$0")/.."; D=$(pwd)
command -v crontab >/dev/null || { echo "cron is not installed. Run: sudo apt install -y cron && sudo systemctl enable --now cron"; exit 1; }
chmod +x scripts/*.sh
grep -q '^RANDOM_SECRET=.\{8,\}' .env || { echo "RANDOM_SECRET=$(openssl rand -hex 16)" >> .env; echo "Added a random RANDOM_SECRET to .env"; }
block="# >>> trader-hydr automation >>>
*/5 * * * * $D/scripts/run_signals.sh
15 * * * * $D/scripts/gate_outlook.sh"
if [ "${1:-}" != "--no-reports" ]; then
  block="$block
10 * * * * $D/scripts/gate_reports.sh"
fi
block="$block
# <<< trader-hydr automation <<<"
( crontab -l 2>/dev/null | sed '/# >>> trader-hydr automation >>>/,/# <<< trader-hydr automation <<</d'; echo "$block" ) | crontab -
echo "Installed:"; crontab -l | sed -n '/>>> trader-hydr/,/<<< trader-hydr/p'
echo; echo "Logs: $D/logs/*.log   Remove later with:  crontab -e  (delete the block)"
