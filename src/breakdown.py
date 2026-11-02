"""Quick look at saved history: python -m src.breakdown [YYYY-MM-DD]   (symbols/percentages only, safe to share)"""
import json, sys, os, collections
from datetime import datetime
from zoneinfo import ZoneInfo
from . import config

h = json.load(open(os.getenv("HISTORY_PATH", "data/trades.json")))
tz = ZoneInfo(config.TIMEZONE)
day = sys.argv[1] if len(sys.argv) > 1 else None
rows = [t for t in h if not day or datetime.fromisoformat(t["date"]).astimezone(tz).date().isoformat() == day]
rows.sort(key=lambda t: t["pnl_pct"])
w = [t["pnl_pct"] for t in rows if t["pnl_pct"] > 0]; l = [t["pnl_pct"] for t in rows if t["pnl_pct"] < 0]
print(f"{len(rows)} trades | {len(w)} wins (avg {sum(w)/max(1,len(w)):+.1f}%) | {len(l)} losses (avg {sum(l)/max(1,len(l)):+.1f}%) | total {sum(t['pnl_pct'] for t in rows):+.1f}%")
print("\nWorst 10:"); [print(f"  {t['symbol']:<12} {t['side']:<7} {t['pnl_pct']:+9.2f}%  {t['date'][:16]}") for t in rows[:10]]
print("\nBest 5:"); [print(f"  {t['symbol']:<12} {t['side']:<7} {t['pnl_pct']:+9.2f}%  {t['date'][:16]}") for t in rows[-5:][::-1]]
byday = collections.defaultdict(list)
for t in h: byday[datetime.fromisoformat(t["date"]).astimezone(tz).date().isoformat()].append(t["pnl_pct"])
print("\nBy day:"); [print(f"  {d}: {len(v):3} trades, {sum(1 for x in v if x>0):3} wins, {sum(v):+9.1f}%") for d, v in sorted(byday.items())]
