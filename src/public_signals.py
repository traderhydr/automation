"""Teaser policy: only N random signals per day go to the FREE channel, and only after a delay.

* Each local day, N random times are drawn (window PUBLIC_WINDOW_START..END, >= 90 min apart).
* The first new signal published after each time is assigned to that slot (its data is stored in the state file).
* It is posted DELAY minutes after the signal itself, so paying members always see it first.
State lives in data/public_signals.json (per day: slots + assignments), so runs every 10 min stay consistent.
"""
import json, os, random
from datetime import datetime, time, timedelta

PATH = "data/public_signals.json"


def load(path=PATH):
    return json.load(open(path)) if os.path.exists(path) else {}


def save(state, path=PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keep = sorted(state)[-7:]
    json.dump({k: state[k] for k in keep}, open(path, "w"), indent=1)


def plan_slots(day, n, start_h, end_h, secret, tz, min_gap_min=90):
    rng = random.Random(f"{day.isoformat()}|{secret}")
    n = max(0, min(n, (end_h - start_h) * 60 // min_gap_min))
    for _ in range(500):
        mins = sorted(rng.sample(range(start_h * 60, end_h * 60), n)) if n else []
        if all(b - a >= min_gap_min for a, b in zip(mins, mins[1:])):
            break
    return [datetime.combine(day, time(m // 60, m % 60), tzinfo=tz).isoformat() for m in mins]


def assign(state_day, signals, now):
    """Give each due, empty slot the first not-yet-used signal published at/after the slot time."""
    used = {v["sig"]["id"] for v in state_day["assigned"].values()}
    for slot in state_day["slots"]:
        if slot in state_day["assigned"] or datetime.fromisoformat(slot) > now:
            continue
        cands = sorted((s for s in signals if s["id"] not in used and datetime.fromisoformat(s["date"]) >= datetime.fromisoformat(slot)),
                       key=lambda s: s["date"])
        if cands:
            state_day["assigned"][slot] = {"sig": cands[0], "posted": False}
            used.add(cands[0]["id"])


def due_to_post(state_day, now, delay_min, lapse_min=240):
    """Assigned signals whose delay has passed (and that aren't hopelessly late)."""
    out = []
    for slot, v in state_day["assigned"].items():
        if v["posted"]:
            continue
        due = datetime.fromisoformat(v["sig"]["date"]) + timedelta(minutes=delay_min)
        if due <= now <= due + timedelta(minutes=lapse_min):
            out.append((slot, v))
    return out


def trade_status(sig, candles, ref_ms):
    """Walk candles after the entry time; report the first thing touched. Honest status for the caption."""
    long_ = sig["side"] == "LONG"
    reached = 0
    for t, o, h, l, c, v in candles:
        if t < ref_ms:
            continue
        hit_sl = (l <= sig["sl"]) if long_ else (h >= sig["sl"])
        n_tp = sum(1 for tp in sig["tps"] if ((h >= tp) if long_ else (l <= tp)))
        if hit_sl and n_tp <= reached:
            return "stopped"
        reached = max(reached, n_tp)
        if hit_sl:
            return f"tp{reached}_then_stop" if reached else "stopped"
    return f"tp{reached}" if reached else "open"
