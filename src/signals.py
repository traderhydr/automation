"""New-signal posts -> parsed signal, risk/reward maths, candles from public exchange APIs."""
import re
import requests
from . import config

NUM = re.compile(r"\d+(?:\.\d+)?")
FILL = re.compile(r"#?([A-Z0-9]{2,15})\s*/\s*(USDT|USDC)\s+Entry\s+(\d+)\s*✅?\s*[\s\S]*?Average Entry Price\s*:\s*(\d+(?:\.\d+)?)", re.I)


def _line(t, key):
    m = re.search(rf"{key}\s*:\s*(.+)", t, re.I)
    return m.group(1).strip() if m else ""


def parse_signals(messages):
    """Own signal template:  Pair: ORDIUSDT / Direction: LONG / Leverage: Cross 25X / Entry: a-b-c / Take Profits: ... / Stop Loss: x"""
    out = []
    for m in messages:
        t = m["text"]
        pair, d = re.search(r"pair\s*:\s*#?([A-Z0-9]{2,15}?)(?:/)?(USDT|USDC)\b", t, re.I), re.search(r"direction\s*:\s*(long|short)", t, re.I)
        entries, tps, sl = NUM.findall(_line(t, "Entry")), NUM.findall(_line(t, r"Take Profits?")), NUM.findall(_line(t, "Stop Loss"))
        if not (pair and d and entries and tps and sl):
            continue
        lev = re.search(r"(\d+)\s*X", _line(t, "Leverage"), re.I)
        out.append({
            "id": m["id"], "date": m["date"], "symbol": pair.group(1).upper() + pair.group(2).upper(),
            "base": pair.group(1).upper(), "side": d.group(1).upper(),
            "leverage": int(lev.group(1)) if lev else None, "strategy": _line(t, "Strategy"),
            "entries": [float(x) for x in entries], "tps": [float(x) for x in tps], "sl": float(sl[0]),
        })
    for s in out:
        find_fill(s, messages)
    return out


def find_fill(sig, messages):
    """Attach the first entry fill (where the trade actually opened) if Cornix reported it in these messages."""
    for m in messages:
        f = FILL.search(m["text"])
        if f and f.group(1).upper() == sig["base"] and f.group(3) == "1" and m["date"] >= sig["date"]:
            sig["fill"] = {"date": m["date"], "price": float(f.group(4))}
            return sig
    return sig


def risk_reward(s):
    """Per-TP reward:risk measured from Entry 1 to the stop. Returns dict with price distances in %."""
    e, sl = s["entries"][0], s["sl"]
    risk = abs(e - sl)
    sign = 1 if s["side"] == "LONG" else -1
    rows = []
    for i, tp in enumerate(s["tps"], 1):
        reward = sign * (tp - e)
        rows.append({"n": i, "price": tp, "rr": round(reward / risk, 2) if risk else None,
                     "pct": round(100 * reward / e, 2)})
    return {"entry": e, "risk_pct": round(100 * risk / e, 2), "tps": rows,
            "final_rr": rows[-1]["rr"] if rows else None}


# ---------- candles: try several free public APIs (Binance blocks US IPs, e.g. GitHub runners) ----------
_MS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}


def _binance(sym, iv, limit, end_ms):
    p = {"symbol": sym, "interval": iv, "limit": limit}
    if end_ms: p["endTime"] = end_ms
    r = requests.get("https://fapi.binance.com/fapi/v1/klines", params=p, timeout=15); r.raise_for_status()
    return [(int(k[0]), *map(float, k[1:6])) for k in r.json()]            # t,o,h,l,c,v


def _bybit(sym, iv, limit, end_ms):
    p = {"category": "linear", "symbol": sym, "interval": iv[:-1] if iv.endswith("m") else str(int(iv[:-1]) * 60),
         "limit": limit}
    if end_ms: p["end"] = end_ms
    r = requests.get("https://api.bybit.com/v5/market/kline", params=p, timeout=15); r.raise_for_status()
    rows = r.json()["result"]["list"]                                       # newest first
    return sorted((int(k[0]), *map(float, k[1:6])) for k in rows)


def _okx(sym, iv, limit, end_ms):
    inst = sym.replace("USDT", "-USDT-SWAP")
    p = {"instId": inst, "bar": iv.replace("h", "H"), "limit": min(limit, 300)}
    if end_ms: p["after"] = end_ms + 1
    r = requests.get("https://www.okx.com/api/v5/market/candles", params=p, timeout=15); r.raise_for_status()
    return sorted((int(k[0]), *map(float, k[1:6])) for k in r.json()["data"])


def _gate(sym, iv, limit, end_ms):
    p = {"contract": sym.replace("USDT", "_USDT"), "interval": iv, "limit": limit}
    if end_ms: p["to"] = end_ms // 1000
    r = requests.get("https://api.gateio.ws/api/v4/futures/usdt/candlesticks", params=p, timeout=15); r.raise_for_status()
    return [(int(k["t"]) * 1000, float(k["o"]), float(k["h"]), float(k["l"]), float(k["c"]), float(k["v"])) for k in r.json()]


PROVIDERS = [("binance", _binance), ("bybit", _bybit), ("okx", _okx), ("gate", _gate)]


def fetch_candles(symbol, interval="15m", limit=96, end_ms=None):
    """Returns (rows, provider_name). rows: (t_ms, o, h, l, c, v) oldest first."""
    last = None
    for name, fn in PROVIDERS:
        try:
            rows = fn(symbol, interval, limit, end_ms)
            if len(rows) >= 10:
                return rows, name
        except Exception as e:      # geo-block, unknown pair on that exchange, rate limit...
            last = e
    raise RuntimeError(f"no candle source worked for {symbol}: {last}")


def signal_caption(sig, status=None, delay_min=None, premium_link=""):
    rr = risk_reward(sig)
    from .signal_chart import fmt
    from . import links
    side_emoji = "🟢" if sig["side"] == "LONG" else "🔴"
    tps = " → ".join(fmt(t["price"]) for t in rr["tps"])
    ents = " / ".join(fmt(e) for e in sig["entries"])
    lev = f" · {sig['leverage']}X" if sig["leverage"] else ""
    tags = f"#{sig['base']} #{sig['symbol']} #CryptoSignals #FuturesTrading #Cornix"
    stat = {"open": "⏳ Still open", "stopped": "🛑 Stopped out"}.get(status or "", "")
    if status and status.startswith("tp") and "_then_" not in status:
        stat = f"✅ TP{status[2:]} reached so far"
    elif status and "_then_stop" in status:
        stat = f"✅ TP{status[2:status.index('_')]} reached, then stopped"
    delay = (f"🕒 <i>Shared {delay_min} min after entry – premium members got this live.</i>\n"
             + (f"🔒 Get every signal in real time: DM {config.PREMIUM_HANDLE} to join premium\n" if premium_link else "")) if delay_min else \
            ("🎁 <i>Free sample from our premium channel – you can take it live.</i>\n"
             + (f"🔒 Premium members get every signal live – DM {config.PREMIUM_HANDLE} to join\n" if premium_link else ""))
    body = (f"⚡ <b>#{sig['base']} {sig['side']}</b>{lev} {side_emoji}\n\n"
            f"🎯 Entry: {ents}\n💰 TPs: {tps}\n🛑 SL: {fmt(sig['sl'])}\n\n"
            f"⚖️ <b>R:R 1:{rr['final_rr']}</b> (to TP{len(rr['tps'])}) · risk {rr['risk_pct']}% price move\n"
            + (f"📌 Status: <b>{stat}</b>\n" if stat else "") + "\n" + delay + f"\n{tags}\n"
            + (links.telegram_block() + "\n\n" if links.telegram_block() else "")
            + "⚠️ Not financial advice. Leveraged trading carries high risk. Not every trade wins.")
    return body, tags


def normalize_candles(candles, ref_price):
    """Exchanges list some coins x1000 / x1e6 (1000PEPE, 1000SHIB...). Rescale to the signal's price scale,
    or return None if the candles don't match the signal at all (never draw a misleading chart)."""
    closes = sorted(c[4] for c in candles)
    med = closes[len(closes) // 2]
    ratio = med / ref_price
    if 0.5 <= ratio <= 2:
        return candles
    for f in (1000, 1e6, 1e-3, 1e-6):
        if 0.5 <= ratio / f <= 2:
            return [(t, o / f, h / f, l / f, c / f, v) for t, o, h, l, c, v in candles]
    return None
