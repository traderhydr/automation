"""Regression tests built from REAL posts of the user's channel. Run: python -m unittest discover tests"""
import unittest
from src import parse
from src.parse import parse_trades
from src.signals import parse_signals, risk_reward

parse._claude_parse = lambda m: []          # never call the API in tests


def msgs(*texts):
    return [{"id": i, "date": f"2026-11-01T{10 + i % 10:02d}:00:00+00:00", "text": t} for i, t in enumerate(texts)]


INJ_SIGNAL = ("⚡ SABBOT REAL ⚡\n\n🧠 Strategy: MACD Cross\n🪙 Pair: INJUSDT\n🧭 Direction: LONG\n⚙️ Leverage: Cross 25X\n"
              "🎯 Entry: 7.091-7.069-6.898-6.777\n💰 Take Profits: 7.133-7.200-7.307-7.491\n🛑 Stop Loss: 6.726")


class RealPosts(unittest.TestCase):
    def test_all_targets_achieved_counts_once(self):
        t = parse_trades(msgs(INJ_SIGNAL, "#INJ/USDT Entry 1 ✅\nAverage Entry Price: 7.091 💵",
            "#INJ/USDT Take-Profit target 1 ✅\nProfit: 16.2713% 📈\nPeriod: 2 hr 1 min ⏰",
            "#INJ/USDT Take-Profit target 3 ✅\nProfit: 28.3437% 📈\nPeriod: 5 hr 7 min ⏰",
            "#INJ/USDT All targets achieved 😎\nProfit: 39.7654% 📈\nPeriod: 5 hr 26 min ⏰"))
        self.assertEqual([(x["symbol"], x["side"], x["pnl_pct"]) for x in t], [("INJUSDT", "LONG", 39.7654)])

    def test_trailing_stop_close_is_a_win(self):
        t = parse_trades(msgs("#SUI/USDT Closed at trailing stoploss after reaching take profit ⚠\nProfit: 5.7895% 📈"))
        self.assertEqual(t[0]["pnl_pct"], 5.7895)

    def test_opposite_signal_close_loss_is_negative(self):
        t = parse_trades(msgs("OKX Futures, MEXC Futures\n#PEPE/USDT Closed due to opposite direction signal ⚠\nLoss: 4.6241% 📉\nPeriod: 2 hr 2 min ⏰"))
        self.assertEqual(t[0]["pnl_pct"], -4.6241)

    def test_opposite_signal_close_profit(self):
        t = parse_trades(msgs("#PEPE/USDT Closed due to opposite direction signal ⚠\nProfit: 21.8224% 📈\nPeriod: 3 hr 2 min ⏰"))
        self.assertEqual(t[0]["pnl_pct"], 21.8224)

    def test_partial_and_entry_posts_ignored(self):
        t = parse_trades(msgs(INJ_SIGNAL, "#ICP/USDT Entry 2 ✅\nAverage Entry Price: 2.514 💵",
                              "#WIF/USDT Take-Profit target 1 ✅\nProfit: 15.302% 📈\nPeriod: 3 hr 51 min ⏰"))
        self.assertEqual(t, [])

    def test_stop_target_hit_is_negative_loss_even_over_100_percent(self):
        aave = ("⚡ SABBOT REAL ⚡\n\n🧠 Strategy: MACD Cross\n🪙 Pair: AAVEUSDT\n🧭 Direction: SHORT\n⚙️ Leverage: Cross 25X\n"
                "🎯 Entry: 133.60-134.00-137.25-139.52\n💰 Take Profits: 132.80-131.53-129.52-126.04\n🛑 Stop Loss: 140.49")
        t = parse_trades(msgs(aave, "#AAVE/USDT Entry 1 ✅\nAverage Entry Price: 133.6 💵",
                              "#AAVE/USDT All entries achieved\nAverage Entry Price: 134.62 💵",
                              "#AAVE/USDT Stop Target Hit ⛔\nLoss: 109.0687% 📉"))
        self.assertEqual([(x["symbol"], x["side"], x["pnl_pct"]) for x in t], [("AAVEUSDT", "SHORT", -109.0687)])

    def test_short_signal_rr(self):
        aave = ("🪙 Pair: AAVEUSDT\n🧭 Direction: SHORT\n⚙️ Leverage: Cross 25X\n🎯 Entry: 133.60-134.00-137.25-139.52\n"
                "💰 Take Profits: 132.80-131.53-129.52-126.04\n🛑 Stop Loss: 140.49")
        rr = risk_reward(parse_signals(msgs(aave))[0])
        self.assertEqual((rr["risk_pct"], rr["tps"][0]["rr"], rr["final_rr"]), (5.16, 0.12, 1.1))

    def test_signal_rr(self):
        s = parse_signals(msgs(INJ_SIGNAL))[0]
        rr = risk_reward(s)
        self.assertEqual((s["symbol"], s["side"], s["leverage"]), ("INJUSDT", "LONG", 25))
        self.assertEqual(rr["final_rr"], 1.1)


if __name__ == "__main__":
    unittest.main()


class CaptionTemplate(unittest.TestCase):
    def test_daily_template_numbers_and_sections(self):
        from src import caption
        today = {"wins": 39, "losses": 9, "trades": 48, "win_rate": 81.3, "total_pct": -286.39, "best": 40.12, "worst": -111.41,
                 "profit_factor": 0.4, "max_drawdown": 300.0, "teaser": {"closed": 0, "wins": 0, "losses": 0, "total": 0, "open": 0, "items": []}}
        month = {"win_rate": 55.6, "total_pct": -721.4, "days": ["a", "b", "c"]}
        t = caption.telegram_report(today, month, "daily", "02 NOV 2026")
        for must in ("DAILY PERFORMANCE REPORT · 02 NOV 2026", "81.3% (39 / 48 trades in profit)", "-286.39%",
                     "3-Day Win Rate: 55.6%", "3-Day Cumulative: -721.4%", "OFFICIAL ECOSYSTEM & LINKS", "Media & Socials", "stop-losses included"):
            self.assertIn(must, t)
        self.assertNotIn("30-Day", t)       # only 3 days of history -> must not claim 30 days


class OwnPosts(unittest.TestCase):
    def test_bot_posts_are_never_parsed_as_trades(self):
        from src.publish import MARK
        own = "⚡ #ORDI LONG · 25X\nR:R 1:1.1 · risk 5.12% price move" + MARK
        self.assertEqual(parse_trades(msgs(own)), [])


class FreeSampleFreshness(unittest.TestCase):
    def test_stale_signal_is_never_assigned(self):
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        from src import public_signals as ps
        tz = ZoneInfo("Asia/Karachi"); now = datetime(2026, 11, 3, 20, 0, tzinfo=tz)
        sd = {"slots": [datetime(2026, 11, 3, 11, 0, tzinfo=tz).isoformat()], "assigned": {}}
        old = {"id": 1, "symbol": "AAAUSDT", "date": (now - timedelta(hours=3)).isoformat()}
        new = {"id": 2, "symbol": "BBBUSDT", "date": (now - timedelta(minutes=4)).isoformat()}
        ps.assign(sd, [old], now, max_age_min=30)
        self.assertEqual(sd["assigned"], {})                      # 3h-old signal ignored
        ps.assign(sd, [old, new], now, max_age_min=30)
        self.assertEqual([v["sig"]["id"] for v in sd["assigned"].values()], [2])


KAVA_SIGNAL = """#KAVA/USDT
SHORT
Timeframe: 5m
Entry Targets:
1) 0.031060
2) 0.031245
3) 0.031430
Take-Profit Targets:
1) 0.030443
2) 0.029826
3) 0.029208
4) 0.027974
Stop Targets:
1) 0.032294
Leverage: Cross (15X)"""


class NewCornixLayout(unittest.TestCase):
    def test_new_layout_signal_parsed(self):
        s = parse_signals(msgs(KAVA_SIGNAL))[0]
        self.assertEqual((s["symbol"], s["side"], s["leverage"], s["timeframe"]), ("KAVAUSDT", "SHORT", 15, "5m"))
        self.assertEqual((len(s["entries"]), len(s["tps"]), s["sl"]), (3, 4, 0.032294))
        rr = risk_reward(s)
        self.assertEqual((rr["risk_pct"], rr["tps"][0]["rr"], rr["final_rr"]), (3.97, 0.5, 2.5))

    def test_new_layout_signal_is_not_a_trade_and_gives_the_side(self):
        t = parse_trades(msgs(KAVA_SIGNAL, "#KAVA/USDT Entry 1 ✅\nAverage Entry Price: 0.03106 💵",
                              "#KAVA/USDT Take-Profit target 1 ✅\nProfit: 9.5% 📈\nPeriod: 4 min ⏰",
                              "#KAVA/USDT All targets achieved 😎\nProfit: 32.1% 📈\nPeriod: 2 hr ⏰"))
        self.assertEqual([(x["symbol"], x["side"], x["pnl_pct"]) for x in t], [("KAVAUSDT", "SHORT", 32.1)])

    def test_old_layout_still_works(self):
        self.assertEqual(parse_signals(msgs(INJ_SIGNAL))[0]["symbol"], "INJUSDT")


class PriceFormatting(unittest.TestCase):
    def test_signal_levels_are_shown_exactly_as_posted(self):
        from src.signals import signal_caption
        doge = ("#DOGE/USDT\nSHORT\nTimeframe: 15m\nEntry Targets:\n1) 0.064790\n2) 0.065037\n3) 0.065283\n"
                "Take-Profit Targets:\n1) 0.063968\n2) 0.063146\n3) 0.062323\n4) 0.060679\nStop Targets:\n1) 0.066434\nLeverage: Cross (15X)")
        cap, _ = signal_caption(parse_signals(msgs(doge))[0], "open", 0, "")
        for must in ("0.06479 / 0.065037 / 0.065283", "0.063968 → 0.063146 → 0.062323 → 0.060679", "0.066434"):
            self.assertIn(must, cap)
        tiny = ("#PEPE/USDT\nLONG\nTimeframe: 5m\nEntry Targets:\n1) 0.000004922\nTake-Profit Targets:\n1) 0.000004951\n"
                "Stop Targets:\n1) 0.000004668\nLeverage: Cross (25X)")
        cap2, _ = signal_caption(parse_signals(msgs(tiny))[0], "open", 0, "")
        self.assertIn("0.000004922", cap2)
        self.assertNotIn("e-06", cap2)


class ShortSignalPost(unittest.TestCase):
    def test_short_format_matches_owner_template(self):
        from src.signals import signal_caption
        doge = ("#DOGE/USDT\nSHORT\nTimeframe: 15m\nEntry Targets:\n1) 0.064790\n2) 0.065037\n3) 0.065283\n"
                "Take-Profit Targets:\n1) 0.063968\n2) 0.063146\n3) 0.062323\n4) 0.060679\nStop Targets:\n1) 0.066434\nLeverage: Cross (15X)")
        cap, _ = signal_caption(parse_signals(msgs(doge))[0], "open", 0, "https://t.me/Hydrzoro")
        plain = cap.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
        expected = """#DOGE SHORT · 15X 🔴

━━━━━━━━━━━━━━━━━━━
• Entry: 0.06479 / 0.065037 / 0.065283
• Take Profits: 0.063968 → 0.063146 → 0.062323 → 0.060679
• Stop Loss: 0.066434
• Risk : Reward: 1 : 2.5 (to TP4) · risk 2.54% price move
• Status: ⏳ Still open

🎁 Free sample from our premium channel. You can take it live.
🔒 Premium members get every signal live: DM @Hydrzoro to join
━━━━━━━━━━━━━━━━━━━"""
        self.assertEqual(plain, expected)
