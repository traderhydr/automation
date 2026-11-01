"""Turn raw channel messages into closed-trade records.

Trade record: {date, symbol, side, pnl_pct}   (pnl_pct = result in %, +/-)

1. Fast regex for common formats, e.g.
     "#BTCUSDT LONG closed ✅ +3.2%"   "ETH/USDT short SL hit -1.5%"   "XAUUSD BUY TP2 +1.8R"
   (R multiples are converted with R_TO_PCT, default 1R = 1%).
2. Anything that looks like a result but didn't match goes to Claude as a fallback.
"""
import json, re
from . import config

R_TO_PCT = 1.0
SYMBOL = re.compile(r"#?\b([A-Z]{2,10}(?:/|-)?(?:USDT|USD|USDC|BTC|INR|EUR|JPY)?)\b")
SIDE = re.compile(r"\b(LONG|SHORT|BUY|SELL)\b", re.I)
PCT = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*%")
RMULT = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*R\b")
RESULT_WORDS = re.compile(r"\b(closed|tp\d?|target|sl hit|stop|profit|loss|booked|hit)\b", re.I)
STOPWORDS = {"LONG", "SHORT", "BUY", "SELL", "TP", "SL", "HIT", "CLOSED", "PROFIT", "LOSS", "ENTRY", "TARGET", "STOP"}


def _regex_parse(msg):
    t = msg["text"]
    side = SIDE.search(t)
    pnl = None
    m = PCT.search(t)
    if m:
        pnl = float(m.group(1))
    else:
        m = RMULT.search(t)
        if m:
            pnl = float(m.group(1)) * R_TO_PCT
    if not side or pnl is None:
        return None
    # a bare positive number after "SL hit"/"loss" is a loss
    if re.search(r"\b(sl hit|stop(ped)? ?loss hit|loss)\b", t, re.I) and pnl > 0 and "+" not in m.group(0):
        pnl = -pnl
    sym = next((s.group(1) for s in SYMBOL.finditer(t.upper()) if s.group(1) not in STOPWORDS), "UNKNOWN")
    return {"date": msg["date"], "symbol": sym.replace("/", "").replace("-", ""),
            "side": side.group(1).upper(), "pnl_pct": pnl}


def _claude_parse(msgs):
    if not (config.ANTHROPIC_API_KEY and msgs):
        return []
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    payload = [{"i": i, "text": m["text"]} for i, m in enumerate(msgs)]
    prompt = (
        "These are messages from a trading signals channel. For each message that reports the FINAL "
        "RESULT of a closed trade, return an object {i, symbol, side (LONG/SHORT), pnl_pct (number, "
        "negative for loss)}. Ignore new signals, entries, chatter and ads. Never invent numbers: if the "
        "result is not explicit, skip it. Reply with ONLY a JSON array.\n\n" + json.dumps(payload)
    )
    r = client.messages.create(model=config.CLAUDE_MODEL, max_tokens=2000,
                               messages=[{"role": "user", "content": prompt}])
    try:
        txt = r.content[0].text
        rows = json.loads(txt[txt.index("["): txt.rindex("]") + 1])
    except Exception:
        return []
    out = []
    for row in rows:
        try:
            m = msgs[int(row["i"])]
            out.append({"date": m["date"], "symbol": str(row["symbol"]).upper(),
                        "side": str(row["side"]).upper(), "pnl_pct": float(row["pnl_pct"])})
        except Exception:
            continue
    return out


def parse_trades(messages):
    trades, leftovers = [], []
    for m in messages:
        t = _regex_parse(m)
        if t:
            trades.append(t)
        elif RESULT_WORDS.search(m["text"]):
            leftovers.append(m)
    return trades + _claude_parse(leftovers)
