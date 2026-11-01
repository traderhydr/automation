"""Eye-catching captions + hashtags. Claude writes them from REAL numbers only."""
import json
from . import config

BASE_TAGS = ["#DailyResults", "#CryptoSignals", "#FuturesTrading", "#Crypto", "#Cornix", "#Bitcoin"]
TRANSPARENCY = "Sum of all closed trades, losses included. Leveraged returns."
DISCLAIMER = "⚠️ Past performance does not guarantee future results. Trading is risky – not financial advice."


PERIOD_LABEL = {"daily": "Today", "weekly": "This week", "monthly": "This month", "yearly": "This year"}


def _teaser_line(st):
    tz = st["teaser"]
    if not (tz["closed"] or tz["open"]):
        return ""
    items = ", ".join(f"{s} {v:+.2f}%" + (" ✅" if v > 0 else " ❌") for s, v in tz["items"])
    return (f"⭐ <b>Free samples we shared:</b> {items}" + (f" · {tz['open']} still open" if tz["open"] else "")
            + f" — {tz['wins']}W/{tz['losses']}L, shown with every other trade, losses included.\n\n")


def _fallback(today, month, period="daily", label=""):
    from datetime import datetime
    emoji = "🔥" if today["total_pct"] >= 0 else "📉"
    head = f"📊 <b>{label} · {period.upper()} RESULTS</b>"
    return {
        "telegram": (f"{head}\n\n✅ <b>{today['wins']}/{today['trades']}</b> trades in profit\n"
                     f"{emoji} Total: <b>{today['total_pct']:+.2f}%</b>\n"
                     f"📈 30-day: <b>{month['total_pct']:+.1f}%</b> · Win rate {month['win_rate']}%\n\n"
                     f"{_teaser_line(today)}<i>{TRANSPARENCY}</i>\n\n👉 Join: {config.JOIN_LINK}"),
        "short": (f"{emoji} {PERIOD_LABEL[period]}: {today['wins']}/{today['trades']} in profit, "
                  f"total {today['total_pct']:+.2f}% (losses included). Join: {config.JOIN_LINK}"),
        "hashtags": BASE_TAGS,
    }


def make_captions(today, month, period="daily", label=""):
    if not config.ANTHROPIC_API_KEY:
        c = _fallback(today, month, period, label)
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        facts = {k: today[k] for k in ("trades", "wins", "losses", "win_rate", "total_pct", "best", "worst")}
        facts["free_samples"] = today["teaser"]
        facts30 = {k: month[k] for k in ("trades", "win_rate", "total_pct", "profit_factor", "max_drawdown")}
        prompt = (
            f"You write social posts for a trading signals channel called '{config.CHANNEL_NAME}'. "
            f"Join link: {config.JOIN_LINK}\n{period.upper()} report stats: {json.dumps(facts)}\nContext (30-day) stats: {json.dumps(facts30)}\n\n"
            f"This is the {period} report for {label}" + (" (a whole year: celebrate the milestone, stay humble)" if period == "yearly" else "") + ". "
            "STYLE: confident, punchy, short lines, emojis like 📊✅🔥📈, headline with the date/period, then X/Y in profit and total. Always include a transparency line (all closed trades, losses included, leveraged returns). Include #DailyResults. "
            "Write: (1) 'telegram': an energetic, emoji-rich post in Telegram HTML (<b>, <i> only), max 700 chars, "
            "ending with a call-to-action to join. (2) 'short': under 240 chars for X/Twitter, with the join link. "
            "(3) 'hashtags': 8-10 relevant hashtags. RULES: use ONLY the numbers given, never promise or imply "
            "guaranteed profit, no 'risk-free'/'guaranteed'. If the period was a loss, be honest and frame it with "
            "the 30-day record and risk management. Reply with ONLY JSON {telegram, short, hashtags}."
        )
        try:
            r = client.messages.create(model=config.CLAUDE_MODEL, max_tokens=1200,
                                       messages=[{"role": "user", "content": prompt}])
            t = r.content[0].text
            c = json.loads(t[t.index("{"): t.rindex("}") + 1])
        except Exception:
            c = _fallback(today, month, period, label)
    tags = " ".join(dict.fromkeys(c.get("hashtags") or BASE_TAGS))
    from . import links
    c["links_tg"], c["links_plain"] = links.telegram_block(), links.plain_block()
    c["telegram"] = f"{c['telegram']}\n\n{tags}\n\n" + (c["links_tg"] + "\n\n" if c["links_tg"] else "") + DISCLAIMER
    c["tags"] = tags
    c["x_tags"] = " ".join(list(dict.fromkeys(c.get("hashtags") or BASE_TAGS))[:3])
    return c
