"""Daily pipeline: fetch -> parse -> stats -> charts -> captions -> publish.

  python main.py                 # real run (honours DRY_RUN)
  python main.py --demo          # fake sample data, no Telegram/API needed (DRY ONLY, never posted)
"""
import argparse, json, os, random
from datetime import datetime, timedelta, timezone
from src import config, stats, charts, caption


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
    ap.add_argument("--hours", type=int, default=24)
    a = ap.parse_args()
    os.makedirs("out", exist_ok=True)

    if a.demo:
        history = demo_trades()
    else:
        from src.fetch import fetch_messages
        from src.parse import parse_trades
        new = parse_trades(fetch_messages(a.hours))
        history = load_history()
        seen = {(t["date"], t["symbol"], t["side"], t["pnl_pct"]) for t in history}
        history += [t for t in new if (t["date"], t["symbol"], t["side"], t["pnl_pct"]) not in seen]
        save_history(history)

    now = datetime.now(timezone.utc)
    def within(days):
        cut = now - timedelta(days=days)
        return [t for t in history if datetime.fromisoformat(t["date"]) >= cut]
    today, month = stats.compute(within(1)), stats.compute(within(30))
    if today["trades"] == 0:
        print("No closed trades in the last 24h – nothing to post."); return

    paths = charts.build_all(today, month, "out")
    cap = caption.make_captions(today, month)
    print(cap["telegram"]); print("\nImages:", paths)

    if a.demo or config.DRY_RUN:
        print("\n[DRY RUN] nothing posted."); return
    from src import publish
    publish.telegram_post(paths, cap["telegram"])
    x_text = f"{cap['short']}\n{cap['tags']}"
    publish.discord_post(paths, cap["short"] + "\n" + cap["tags"])
    publish.x_post(paths, x_text)
    print("Posted.")


if __name__ == "__main__":
    main()
