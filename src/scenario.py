"""Support / resistance detection + scenario text for a market-outlook chart (algorithmic, no predictions)."""
import statistics


def _pivots(c, k=3):
    hi, lo = [], []
    for i in range(k, len(c) - k):
        if c[i][2] == max(x[2] for x in c[i - k:i + k + 1]): hi.append((i, c[i][2]))
        if c[i][3] == min(x[3] for x in c[i - k:i + k + 1]): lo.append((i, c[i][3]))
    return hi, lo


def _cluster(points, n, tol=0.004):
    """Group pivot prices within tol of each other; score = touches + recency. Returns [(price, touches, score)]."""
    cl = []
    for i, p in sorted(points, key=lambda x: x[1]):
        if cl and abs(p - cl[-1]["p"]) / cl[-1]["p"] <= tol:
            g = cl[-1]; g["ps"].append(p); g["is"].append(i); g["p"] = sum(g["ps"]) / len(g["ps"])
        else:
            cl.append({"p": p, "ps": [p], "is": [i]})
    return [(g["p"], len(g["ps"]), len(g["ps"]) + 1.5 * max(g["is"]) / n) for g in cl]


def analyse(candles):
    """candles: (t,o,h,l,c,v) oldest first, ideally 1h x ~100. Returns dict of levels + 24h stats."""
    n = len(candles)
    last = candles[-1][4]
    day = candles[-24:] if n >= 24 else candles
    ref = candles[-25][4] if n >= 25 else candles[0][1]
    atr = statistics.mean(c[2] - c[3] for c in candles[-14:])
    hi_p, lo_p = _pivots(candles)
    res_cl = [x for x in _cluster(hi_p, n) if x[0] > last * 1.004]
    sup_cl = [x for x in _cluster(lo_p, n) if x[0] < last * 1.004]
    rng_hi, rng_lo = max(c[2] for c in candles), min(c[3] for c in candles)
    # resistance: strongest cluster above price (ties -> nearer); else the range high
    resistance = max(res_cl, key=lambda x: (x[2], -x[0]))[0] if res_cl else rng_hi
    resistance = max(resistance, last * 1.005)
    # support zone: strongest cluster below price within 6%; else most recent swing low
    near = [x for x in sup_cl if x[0] > last * 0.94] or sup_cl
    zone_mid = max(near, key=lambda x: (x[2], x[0]))[0] if near else (lo_p[-1][1] if lo_p else rng_lo)
    half = max(atr * 0.45, zone_mid * 0.0012)
    zone = (zone_mid - half, zone_mid + half)
    # major support: next cluster at least 3% below the zone, else the range low
    deep = [x for x in sup_cl if x[0] < zone[0] * 0.97]
    major = max(deep, key=lambda x: (x[1], x[0]))[0] if deep else min(rng_lo, zone[0] * 0.95)
    if last < zone[0]: status = "below"
    elif last > zone[1] * 1.012: status = "above"
    elif last > zone[1]: status = "near"
    else: status = "inside"
    return {"last": last, "chg24": round(100 * (last - ref) / ref, 2), "high24": max(c[2] for c in day),
            "low24": min(c[3] for c in day), "vol24": sum(c[5] * c[4] for c in day),   # approx. quote volume
            "resistance": resistance, "zone": zone, "zone_mid": zone_mid, "major": major, "status": status}


def key_level_text(base, lv, fmt):
    z = fmt(lv["zone_mid"]); m = fmt(lv["major"])
    if lv["status"] == "below":
        return (f"{base} has slipped under its support zone near {z}.",
                f"Reclaiming it keeps a bounce alive; staying below could open the door toward {m}.")
    if lv["status"] == "above":
        return (f"{base} is trading above its support zone near {z}.",
                f"A pullback that holds there favours a push toward {fmt(lv['resistance'])}; a break could open {m}.")
    return (f"{base} is testing a critical support zone around {z}.",
            f"Break below could open the door for a deeper move toward {m}.")


def human(v):
    for d, s in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= d: return f"{v / d:.2f}{s}"
    return f"{v:.0f}"


def scenario_caption(base, lv, fmt):
    k1, k2 = key_level_text(base, lv, fmt)
    ch = lv["chg24"]; arrow = "🔴" if ch < 0 else "🟢"
    tags = f"#{base} #{base}USDT #CryptoAnalysis #Bitcoin #TradingSetup" if base == "BTC" else f"#{base} #{base}USDT #CryptoAnalysis #TradingSetup"
    return (f"📊 <b>#{base} OUTLOOK</b> · {fmt(lv['last'])} ({arrow} {ch:+.2f}% 24h)\n\n"
            f"🛡 Support zone: {fmt(lv['zone'][0])} – {fmt(lv['zone'][1])}\n🚧 Resistance: {fmt(lv['resistance'])}\n"
            f"🔻 Major support: {fmt(lv['major'])}\n\n"
            f"🟢 <b>Bounce:</b> support holds → room toward {fmt(lv['resistance'])}\n"
            f"🔴 <b>Dump:</b> support breaks → retest near {fmt(lv['major'])}\n\n"
            f"💡 {k1} {k2}\n\n{tags}\n"
            f"⚠️ Levels are algorithmic scenarios, not predictions or financial advice."), tags
