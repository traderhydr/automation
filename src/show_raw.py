"""Show the raw channel posts for one coin, oldest first – to check how the parser counted a trade.
    python -m src.show_raw JUP [hours]        (only trade posts, no keys; safe to paste)"""
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from . import config
from .fetch import fetch_messages

coin = sys.argv[1].upper().replace("USDT", "").replace("/", "")
hours = int(sys.argv[2]) if len(sys.argv) > 2 else 72
tz = ZoneInfo(config.TIMEZONE)
for m in fetch_messages(hours):
    t = m["text"].upper()
    if f"#{coin}/USDT" in t or f"PAIR: {coin}USDT" in t:
        when = datetime.fromisoformat(m["date"]).astimezone(tz).strftime("%m-%d %H:%M")
        body = " ⏎ ".join(l.strip() for l in m["text"].splitlines() if l.strip())
        print(f"[{when}] {body[:260]}")
