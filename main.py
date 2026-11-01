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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--period", choices=list(PERIODS), default="daily")
    ap.add_argument("--hours", type=int, default=24, help="how far back to fetch new messages")
    a = ap.parse_args()
    os.makedirs("out", exist_ok=True)

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
