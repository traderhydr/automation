"""Daily pipeline: fetch -> parse -> stats -> charts -> captions -> publish.

  python main.py --period daily|weekly|monthly|yearly   # real run (honours DRY_RUN)
  python main.py --demo          # fake sample data, no Telegram/API needed (DRY ONLY, never posted)
"""
import argparse, json, os, random
from datetime import datetime, timedelta, timezone
from src import config, stats, charts, caption
from src.periods import PERIODS


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


def run_signals(a):
    """Post a QNT-style chart (entry, TPs, SL, R:R) for each NEW signal in the private channel."""
    from src import signals, signal_chart
    state_path = "data/posted_signals.json"
    posted = set(json.load(open(state_path))) if os.path.exists(state_path) else set()
    if a.demo:
        msgs, demo_cs = demo_signal_data()
    else:
        from src.fetch import fetch_messages
        msgs, demo_cs = fetch_messages(max(1, a.hours)), None
    now = datetime.now(timezone.utc)
    for sig in signals.parse_signals(msgs):
        age_min = (now - datetime.fromisoformat(sig["date"])).total_seconds() / 60
        if sig["id"] in posted or age_min > config.SIGNAL_MAX_AGE_MIN:
            continue
        iv = config.SIGNAL_INTERVAL
        if demo_cs:
            candles, src = demo_cs, "demo"
        else:
            ref = datetime.fromisoformat(sig.get("fill", {}).get("date", sig["date"])).timestamp() * 1000
            candles, src = signals.fetch_candles(sig["symbol"], iv, 96, int(ref + 2 * signals._MS[iv] * 1000))
        candles = signals.normalize_candles(candles, sig["entries"][0])
        if candles is None:
            print(f"Skipping {sig['symbol']}: exchange prices don't match the signal's price scale."); continue
        path = f"out/signal_{sig['id']}.png"
        signal_chart.signal_chart(sig, candles, iv, src, path)
        cap, tags = signals.signal_caption(sig)
        print(cap, "\nImage:", path)
        if a.demo or config.DRY_RUN:
            print("[DRY RUN] nothing posted.\n"); continue
        from src import publish
        publish.telegram_photo(path, cap)
        publish.discord_post([path], f"{sig['base']} {sig['side']} | R:R 1:{signals.risk_reward(sig)['final_rr']}\n{tags}")
        publish.x_post([path], f"⚡ #{sig['base']} {sig['side']} | R:R 1:{signals.risk_reward(sig)['final_rr']} | SL & TPs on chart", " ".join(tags.split()[:3]))
        posted.add(sig["id"]); os.makedirs("data", exist_ok=True); json.dump(sorted(posted), open(state_path, "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--signals", action="store_true", help="post charts for NEW signals instead of a report")
    ap.add_argument("--period", choices=list(PERIODS), default="daily")
    ap.add_argument("--hours", type=int, default=24, help="how far back to fetch new messages")
    a = ap.parse_args()
    os.makedirs("out", exist_ok=True)
    if a.signals:
        return run_signals(a)

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
    now = datetime.now(timezone.utc)
    def within(days):
        cut = now - timedelta(days=days)
        return [t for t in history if datetime.fromisoformat(t["date"]) >= cut]
    days, bucket = PERIODS[a.period][0], PERIODS[a.period][1]
    today, month = stats.compute(within(days), bucket), stats.compute(within(30))
    if today["trades"] == 0:
        print(f"No closed trades in the {a.period} window – nothing to post."); return

    paths = charts.build_all(today, month, a.period, "out")
    cap = caption.make_captions(today, month, a.period)
    print(cap["telegram"]); print("\nImages:", paths)

    if a.demo or config.DRY_RUN:
        print("\n[DRY RUN] nothing posted."); return
    from src import publish
    publish.telegram_post(paths, cap["telegram"])
    publish.discord_post(paths, cap["short"] + "\n" + cap["tags"])
    publish.x_post(paths, cap["short"], cap["x_tags"])
    print("Posted.")


if __name__ == "__main__":
    main()
