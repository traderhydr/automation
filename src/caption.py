"""Eye-catching captions + hashtags. Claude writes them from REAL numbers only."""
import json
from . import config

BASE_TAGS = ["#DailyResults", "#CryptoSignals", "#FuturesTrading", "#Crypto", "#Cornix", "#Bitcoin"]
TRANSPARENCY = "Sum of all closed trades, losses included. Leveraged returns."
DISCLAIMER = "⚠️ Past performance does not guarantee future results. Trading is risky – not financial advice."


SEP = "━━━━━━━━━━━━━━━━━━━"
PERIOD_WORD = {"daily": "DAILY", "weekly": "WEEKLY", "monthly": "MONTHLY", "yearly": "YEARLY"}


def _intro(today):
    if today["total_pct"] >= 0:
        return "Real results, zero cherry-picking. Every closed trade is counted: wins and losses."
    if today["win_rate"] >= 60:
        return ("Real results, zero cherry-picking. Even on high-win days, managing drawdowns and "
                "leverage discipline is part of the game.")
    return "Real results, zero cherry-picking. Red days happen: risk management is the job."


def telegram_report(today, month, period, label):
    """Layout supplied by the channel owner (clean spacing). All numbers come from the real trade history."""
    from . import links
    pw, Pw = PERIOD_WORD[period], PERIOD_WORD[period].title()
    net = "📈" if today["total_pct"] >= 0 else "📉"
    rows = [f"• {Pw} Win Rate: {today['win_rate']}% ({today['wins']} / {today['trades']} trades in profit) ✅",
            f"• {Pw} Net PnL: {today['total_pct']:+.2f}% {net}"]
    if period == "daily":
        n = max(1, min(30, len(month["days"])))      # honest label: days of history actually tracked (max 30)
        rows += [f"• {n}-Day Win Rate: {month['win_rate']}% 📈", f"• {n}-Day Cumulative: {month['total_pct']:+.1f}%"]
    else:
        pf = today["profit_factor"] if today["profit_factor"] is not None else "n/a"
        rows += [f"• Profit Factor: {pf}", f"• Best / Worst Trade: {today['best']:+.2f}% / {today['worst']:+.2f}%",
                 f"• Max Drawdown: -{today['max_drawdown']}%"]
    tz = today["teaser"]
    if tz["closed"] or tz["open"]:
        items = ", ".join(f"{s} {v:+.2f}%" + (" ✅" if v > 0 else " ❌") for s, v in tz["items"])
        rows.append(f"• ⭐ Free Samples Shared: {items}" + (f" · {tz['open']} still open" if tz["open"] else ""))
    note = f"(Figures reflect the sum of all closed trades, stop-losses included. {config.PNL_NOTE}.)"
    parts = [f"<b>📊 {pw} PERFORMANCE REPORT · {label}</b>", SEP + "\n" + _intro(today),
             "<b>⚡ THE BREAKDOWN</b>", "\n".join(rows), note + "\n" + SEP]
    eco = links.ecosystem_block()
    if eco:
        parts += [eco, SEP]
    return "\n\n".join(parts)


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
    # Telegram post = the owner's template (exact real numbers); Claude/fallback text is only used for X + hashtags
    c["telegram"] = "\n\n".join(x for x in (telegram_report(today, month, period, label), tags, links.disclosure(), DISCLAIMER) if x)
    c["tags"] = tags
    c["x_tags"] = " ".join(list(dict.fromkeys(c.get("hashtags") or BASE_TAGS))[:3])
    return c


def clean_post(title, body_blocks, tags, closing_disclaimer):
    """Same clean layout as the report template: title, ━━━ separators, blank lines, grouped links, disclosure."""
    from . import links
    parts = [f"<b>{title}</b>", SEP + "\n" + "\n\n".join(b for b in body_blocks if b) + "\n" + SEP]
    eco = links.ecosystem_block()
    if eco:
        parts += [eco, SEP]
    parts += [x for x in (tags, links.disclosure(), closing_disclaimer) if x]
    return "\n\n".join(parts)
