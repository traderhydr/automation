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
