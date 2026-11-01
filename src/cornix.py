"""Parser for Cornix bot updates posted in a Telegram channel.

Typical Cornix posts (layout may vary a little by version/settings):

  Signal:   ⚡⚡ #BTC/USDT ⚡⚡ / Signal Type: Regular (Long) / Leverage: Isolated (10X) / Entry Orders: ...
  Update:   #BTC/USDT  Take-Profit target 1 ✅  Profit: 25.3%  Period: 2 Hours 5 Minutes
  Final:    #BTC/USDT  All take-profit targets achieved 😎  Profit: 85.5%  Period: ...
            #ETH/USDT  Stop Target Hit ⛔  Loss: 12.5%  Period: ...
            #SOL/USDT  Closed due to other reason ⚠  Profit/Loss: -3.1%

A trade counts ONCE, when it reaches a final state (all TPs / stop / closed). Intermediate
"Take-Profit target N" and entry messages are recognised and ignored so nothing is double counted.
Cornix % figures are what Cornix shows (normally already multiplied by leverage).
"""
import re

PAIR = re.compile(r"#?\b([A-Z0-9]{2,15})\s*/\s*([A-Z0-9]{2,10})\b")
PNL = re.compile(r"\b(profit|loss|profit/loss|p/l|roi)\b\s*[:=]?\s*([+-]?\d+(?:[.,]\d+)?)\s*%", re.I)
SIGNAL_SIDE = re.compile(r"signal type\s*:?\s*[^\n(]*\((long|short)\)", re.I)
SIGNAL_MARK = re.compile(r"signal type|entry orders|entry zone|entry targets?\b|take-profit targets?\s*:", re.I)
FINAL = re.compile(r"all take-profit targets? (?:achieved|reached|hit)|stop(?:-| )?(?:loss|target)? (?:target )?hit|"
                   r"stop target|closed (?:due to|at|manually|by)|closed", re.I)
PARTIAL = re.compile(r"take-profit target \d+|tp ?\d+ (?:hit|reached|achieved)|entry target \d+|entry \d+ (?:achieved|reached)|"
                     r"entry (?:order )?(?:achieved|filled)|cancelled|canceled|moved to break", re.I)


def is_cornix(text):
    return bool(PAIR.search(text) and (SIGNAL_MARK.search(text) or PNL.search(text) or PARTIAL.search(text) or FINAL.search(text)))


def parse_cornix(messages):
    """Returns (trades, handled_ids). trades: {id,date,symbol,side,pnl_pct}"""
    sides = {}
    for m in messages:  # remember side per symbol from signal posts in this batch
        p, s = PAIR.search(m["text"]), SIGNAL_SIDE.search(m["text"])
        if p and s:
            sides[p.group(1) + p.group(2)] = s.group(1).upper()
    trades, handled = [], set()
    for m in messages:
        t = m["text"]
        if not is_cornix(t):
            continue
        handled.add(m["id"])
        if SIGNAL_MARK.search(t) and not PNL.search(t):
            continue  # new signal
        p, pnl = PAIR.search(t), PNL.search(t)
        if not (p and pnl):
            continue
        if PARTIAL.search(t) and not FINAL.search(t.replace("Take-Profit target", "")):
            continue  # intermediate TP/entry update
        if not FINAL.search(t):
            continue
        val = float(pnl.group(2).replace(",", "."))
        if pnl.group(1).lower() == "loss":
            val = -abs(val)
        sym = p.group(1) + p.group(2)
        trades.append({"id": m["id"], "date": m["date"], "symbol": sym,
                       "side": sides.get(sym, "UNKNOWN"), "pnl_pct": val})
    return trades, handled
