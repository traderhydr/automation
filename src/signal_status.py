"""Shows today's free-sample plan and what happened to it (no secrets, coin names only).   python -m src.signal_status"""
import json, os
from datetime import datetime
from zoneinfo import ZoneInfo
from . import config, public_signals as ps

tz = ZoneInfo(config.TIMEZONE)
now = datetime.now(tz)
print(f"Now: {now:%Y-%m-%d %H:%M} {config.TIMEZONE}")
print(f"Policy: {config.PUBLIC_SIGNALS_PER_DAY}/day between {config.PUBLIC_WINDOW_START}:00 and {config.PUBLIC_WINDOW_END}:00, "
      f"delay {config.PUBLIC_SIGNAL_DELAY_MIN} min, only signals <= {config.PUBLIC_SIGNAL_MAX_AGE_MIN} min old")
print(f"Post to: {', '.join(config.CHANNELS_SIGNALS) or '(NO CHANNELS SET!)'}")
state = ps.load()
day = now.date().isoformat()
if day not in state:
    raise SystemExit(f"\nNo plan for {day} yet: the signals job has not run today (check cron / logs/signals.log).")
sd = state[day]
print(f"\nToday's random times: {[s[11:16] for s in sd['slots']]}")
for slot in sd["slots"]:
    t = datetime.fromisoformat(slot); a = sd["assigned"].get(slot)
    if t > now:
        print(f"  {t:%H:%M}  waiting (not reached yet)")
    elif not a:
        print(f"  {t:%H:%M}  PASSED but no fresh signal assigned yet (needs a new signal <= {config.PUBLIC_SIGNAL_MAX_AGE_MIN} min old)")
    else:
        s = a["sig"]; age = (now - datetime.fromisoformat(s["date"])).total_seconds() / 60
        state_txt = "POSTED" if a["posted"] else f"assigned, NOT posted yet (channels done: {a.get('done_chats', [])})"
        print(f"  {t:%H:%M}  {s['symbol']} {s['side']} (signal {age:.0f} min old) -> {state_txt}")
