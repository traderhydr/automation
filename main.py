"""Daily pipeline: fetch -> parse -> stats -> charts -> captions -> publish.

  python main.py --period daily|weekly|monthly|yearly   # real run (honours DRY_RUN)
  python main.py --demo          # fake sample data, no Telegram/API needed (DRY ONLY, never posted)
"""
import argparse, json, os, random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from src import config, stats, charts, caption
from src.periods import PERIODS, window


def load_history(path="data/trades.json"):
    return json.load(open(path)) if os.path.exists(path) else []


def save_history(trades, path="data/trades.json"):
    os.makedirs("data", exist_ok=True)
    json.dump(trades, open(path, "w"), indent=1)


def demo_trades():
    random.seed(7)
    now = datetime.now(timezone.utc)
    return [{"date": (now - timedelta(days=d, hours=h)).isoformat(), "symbol": random.choice(["BTCUSDT", "ETHUSDT", "XAUUSD"]),
             "side": random.choice(["LONG", "SHORT"]), "pnl_pct": round(random.choice([-1, -1.5, 2, 3, 4.5, 1.2]), 2)}
            for d in range(30) for h in range(random.randint(1, 3))]


def demo_signal_data():
    raw = ("⚡ SABBOT REAL ⚡\n\n🧠 Strategy: MACD Cross\n🪙 Pair: ORDIUSDT\n🧭 Direction: LONG\n⚙️ Leverage: Cross 25X\n"
           "🎯 Entry: 3.533-3.523-3.437-3.377\n💰 Take Profits: 3.554-3.588-3.641-3.733\n🛑 Stop Loss: 3.352")
    now = datetime.now(timezone.utc)
    msgs = [{"id": 1, "date": now.isoformat(), "text": raw},
            {"id": 2, "date": now.isoformat(), "text": "#ORDI/USDT Entry 1 ✅\nAverage Entry Price: 3.533 💵"}]
    random.seed(3); price, t0, cs = 3.62, int(now.timestamp() * 1000) - 96 * 900000, []
    for i in range(97):
        o = price; c = o * (1 + random.gauss(-0.0006 if i < 92 else 0.0008, 0.004))
        cs.append((t0 + i * 900000, o, max(o, c) * 1.001, min(o, c) * 0.999, c, 1)); price = c
    return msgs, cs


def _post_signal(sig, status_candles_src, iv, status, delay_min, a):
    from src import signals, signal_chart, publish
    candles, src = status_candles_src
    path = f"out/signal_{sig['id']}.png"
    signal_chart.signal_chart(sig, candles, iv, src, path)
    cap, tags = signals.signal_caption(sig, status, delay_min, config.PREMIUM_LINK)
    print(cap, "\nImage:", path)
    if a.demo or config.DRY_RUN:
        print("[DRY RUN] nothing posted.\n"); return False
    rr = signals.risk_reward(sig)["final_rr"]
    publish.telegram_photo(path, cap)
    publish.discord_post([path], f"{sig['base']} {sig['side']} | R:R 1:{rr} (free sample)\n{tags}")
    publish.x_post([path], f"⚡ #{sig['base']} {sig['side']} | R:R 1:{rr} | free sample from our premium channel. Entry, TPs & SL on chart 👇" if not delay_min else f"⚡ #{sig['base']} {sig['side']} | R:R 1:{rr} | shared {delay_min} min after premium members. Details on chart 👇", " ".join(tags.split()[:3]))
    return True


def run_signals(a):
    """FREE-channel samples: N random signals/day, posted immediately (or DELAY min later if PUBLIC_SIGNAL_DELAY_MIN > 0)."""
    from src import signals, public_signals as ps
    iv, delay = config.SIGNAL_INTERVAL, config.PUBLIC_SIGNAL_DELAY_MIN
    if a.demo:
        msgs, demo_cs = demo_signal_data()
        sig = signals.parse_signals(msgs)[0]
        cs = signals.normalize_candles(demo_cs, sig["entries"][0])
        ref = datetime.fromisoformat(sig["fill"]["date"]).timestamp() * 1000 - 3 * 900000
        status = ps.trade_status(sig, cs, ref)
        _post_signal(sig, (cs, "demo"), iv, status, delay, a); return

    from src.fetch import fetch_messages
    tz = ZoneInfo(config.TIMEZONE)
    now = datetime.now(tz)
    msgs = fetch_messages(max(1, a.hours))
    sigs = signals.parse_signals(msgs)
    state = ps.load()
    day = now.date().isoformat()
    sd = state.setdefault(day, {"slots": ps.plan_slots(now.date(), config.PUBLIC_SIGNALS_PER_DAY, config.PUBLIC_WINDOW_START,
                                                       config.PUBLIC_WINDOW_END, config.RANDOM_SECRET, tz), "assigned": {}})
    if config.PUBLIC_SIGNALS_PER_DAY <= 0:          # unlimited mode: every signal becomes a slot of its own
        for s in sigs:
            sd["assigned"].setdefault(f"all-{s['id']}", {"sig": s, "posted": False})
    else:
        ps.assign(sd, sigs, now)
    print(f"{day} slots: {sd['slots']} | assigned: {[v['sig']['symbol'] + ('' if not v['posted'] else '✓') for v in sd['assigned'].values()]}")
    changed = True
    for slot, v in ps.due_to_post(sd, now, delay):
        sig = signals.find_fill(v["sig"], msgs)
        ref = datetime.fromisoformat(sig.get("fill", {}).get("date", sig["date"])).timestamp() * 1000
        try:
            candles, src = signals.fetch_candles(sig["symbol"], iv, 96)       # up to NOW, so the chart shows what happened since
        except Exception as e:
            print(f"{sig['symbol']}: no candles ({e}); will retry next run"); continue
        candles = signals.normalize_candles(candles, sig["entries"][0])
        if candles is None:
            print(f"Skipping {sig['symbol']}: exchange prices don't match the signal's price scale."); v["posted"] = True; continue
        if _post_signal(sig, (candles, src), iv, ps.trade_status(sig, candles, ref), delay, a):
            v["posted"] = True
    if not config.DRY_RUN:
        ps.save(state)


def run_scenario(a):
    """Support/resistance 'bounce vs dump' chart per symbol, posted to the public channel."""
    from src import signals, scenario, scenario_chart
    from src.signal_chart import fmt
    for sym in [s.strip().upper() for s in a.scenario.split(",") if s.strip()]:
        base, iv = sym.replace("USDT", ""), config.SCENARIO_INTERVAL
        if a.demo:
            _, cs = demo_signal_data(); cs = [(t, o * 19000, h * 19000, l * 19000, c * 19000, 1500) for t, o, h, l, c, _ in cs]
            src = "demo"
        else:
            cs, src = signals.fetch_candles(sym, iv, 100)
        if len(cs) < 40:
            print(f"{sym}: not enough candles"); continue
        lv = scenario.analyse(cs)
        path = f"out/scenario_{base}.png"
        scenario_chart.scenario_chart(base, cs, lv, iv, src, path)
        cap, tags = scenario.scenario_caption(base, lv, fmt)
        print(cap, "\nImage:", path)
        if a.demo or config.DRY_RUN:
            print("[DRY RUN] nothing posted.\n"); continue
        from src import publish
        publish.telegram_photo(path, cap)
        publish.discord_post([path], f"{base} outlook\n{tags}")
        publish.x_post([path], f"📊 #{base} outlook: {fmt(lv['last'])} ({lv['chg24']:+.2f}% 24h). Support {fmt(lv['zone_mid'])} | Resistance {fmt(lv['resistance'])}. Bounce or dump? 👇", " ".join(tags.split()[:3]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--scenario", metavar="SYMBOLS", help="market outlook chart(s), e.g. BTCUSDT,ETHUSDT")
    ap.add_argument("--signals", action="store_true", help="post charts for NEW signals instead of a report")
    ap.add_argument("--period", choices=list(PERIODS), default="daily")
    ap.add_argument("--hours", type=int, default=30, help="how far back to fetch new messages")
    ap.add_argument("--force", action="store_true", help="post even if this exact report was already posted")
    ap.add_argument("--date", help="any date (YYYY-MM-DD) inside the period to report; default today (in TIMEZONE)")
    a = ap.parse_args()
    os.makedirs("out", exist_ok=True)
    if a.signals:
        return run_signals(a)
    if a.scenario:
        return run_scenario(a)

    if a.demo:
        history = demo_trades()
    else:
        from src.fetch import fetch_messages
        from src.parse import parse_trades
        new = parse_trades(fetch_messages(a.hours))
        history = load_history()
        key = lambda t: t.get("id") or (t["date"], t["symbol"], t["pnl_pct"])
        seen = {key(t) for t in history}
        history += [t for t in new if key(t) not in seen]
        save_history(history)

    scale = config.MARGIN_PER_TRADE_PCT / 100
    history = [{**t, "pnl_pct": t["pnl_pct"] * scale} for t in history]
    tz = ZoneInfo(config.TIMEZONE)
    ref = date.fromisoformat(a.date) if a.date else datetime.now(tz).date()
    start, end, label = window(a.period, ref, tz)
    # work in local time so "a day" means a calendar day in TIMEZONE
    local = [{**t, "date": datetime.fromisoformat(t["date"]).astimezone(tz).isoformat()} for t in history]
    inside = lambda t, s, e: s <= datetime.fromisoformat(t["date"]) < e
    bucket = PERIODS[a.period][1]
    today = stats.compute([t for t in local if inside(t, start, end)], bucket)
    month = stats.compute([t for t in local if inside(t, end - timedelta(days=30), end)])
    rkey = f"{a.period}:{start:%Y-%m-%d}"
    rpath = "data/posted_reports.json"
    done = set(json.load(open(rpath))) if os.path.exists(rpath) else set()
    if rkey in done and not a.force and not a.demo and not config.DRY_RUN:
        print(f"{rkey} was already posted – skipping (use --force to repost)."); return
    print(f"{a.period} report {label} ({start:%Y-%m-%d %H:%M} -> {end:%Y-%m-%d %H:%M} {config.TIMEZONE}): {today['trades']} trades")
    if today["trades"] == 0:
        print("No closed trades in this window – nothing to post."); return

    paths = charts.build_all(today, month, a.period, "out", label)
    cap = caption.make_captions(today, month, a.period, label)
    print(cap["telegram"]); print("\nImages:", paths)

    if a.demo or config.DRY_RUN:
        print("\n[DRY RUN] nothing posted."); return
    from src import publish
    publish.telegram_post(paths, cap["telegram"])
    publish.discord_post(paths, cap["short"] + "\n" + cap["tags"])
    publish.x_post(paths, cap["short"], cap["x_tags"])
    done.add(rkey); os.makedirs("data", exist_ok=True); json.dump(sorted(done), open(rpath, "w"))
    print("Posted.")


if __name__ == "__main__":
    main()
