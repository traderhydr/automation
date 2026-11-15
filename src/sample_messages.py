"""What kinds of messages is the channel posting?   python -m src.sample_messages [hours] [how_many]
Prints a count per message type and the newest messages (first line only, with age). Trade info only, no secrets."""
import re, sys, collections
from datetime import datetime, timezone
from .fetch import fetch_messages

hours = int(sys.argv[1]) if len(sys.argv) > 1 else 6
n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
msgs = fetch_messages(hours)


def kind(t):
    low = t.lower()
    if "pair" in low and ("direction" in low or "entry" in low): return "NEW SIGNAL"
    if re.search(r"entry \d+|all entries", low): return "entry fill"
    if "take-profit target" in low: return "take-profit hit"
    if "all targets achieved" in low or "all take-profit" in low: return "all targets"
    if "stop target hit" in low: return "stop hit"
    if "closed" in low: return "closed"
    return "OTHER"


now = datetime.now(timezone.utc)
cnt = collections.Counter(kind(m["text"]) for m in msgs)
print(f"{len(msgs)} messages in the last {hours}h: " + ", ".join(f"{k}: {v}" for k, v in cnt.most_common()))
sig = [m for m in msgs if kind(m["text"]) == "NEW SIGNAL"]
print("newest NEW SIGNAL:", f"{(now - datetime.fromisoformat(sig[-1]['date'])).total_seconds() / 60:.0f} min ago" if sig else "none in this window")
print(f"\nNewest {n} messages (oldest first):")
for m in msgs[-n:]:
    age = (now - datetime.fromisoformat(m["date"])).total_seconds() / 60
    first = " | ".join(l.strip() for l in m["text"].splitlines() if l.strip())[:110]
    print(f"  {age:5.0f} min ago  [{kind(m['text'])}]  {first}")
