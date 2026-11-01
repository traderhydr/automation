"""Eye-catching captions + hashtags. Claude writes them from REAL numbers only."""
import json
from . import config

BASE_TAGS = ["#trading", "#signals", "#cryptotrading", "#forex", "#daytrading", "#profit"]
DISCLAIMER = "⚠️ Past performance does not guarantee future results. Trading is risky – not financial advice."


PERIOD_LABEL = {"daily": "Today", "weekly": "This week", "monthly": "This month", "yearly": "This year"}


def _fallback(today, month, period="daily"):
    emoji = "🟢🔥" if today["total_pct"] >= 0 else "📉"
    return {
        "telegram": (f"{emoji} <b>{period.title()} Report</b>\n\n"
                     f"{PERIOD_LABEL[period]}: <b>{today['total_pct']:+.2f}%</b> ({today['wins']}W/{today['losses']}L, "
                     f"{today['win_rate']}% win rate)\n"
                     f"30 days: <b>{month['total_pct']:+.1f}%</b> | Profit factor {month['profit_factor']}\n\n"
                     f"👉 Want the live entries? Join: {config.JOIN_LINK}"),
        "short": (f"{emoji} Today {today['total_pct']:+.2f}% | 30d {month['total_pct']:+.1f}% | "
                  f"{month['win_rate']}% win rate. Join: {config.JOIN_LINK}"),
        "hashtags": BASE_TAGS,
    }


def make_captions(today, month, period="daily"):
    if not config.ANTHROPIC_API_KEY:
        c = _fallback(today, month, period)
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        facts = {k: today[k] for k in ("trades", "wins", "losses", "win_rate", "total_pct", "best", "worst")}
        facts30 = {k: month[k] for k in ("trades", "win_rate", "total_pct", "profit_factor", "max_drawdown")}
        prompt = (
            f"You write social posts for a trading signals channel called '{config.CHANNEL_NAME}'. "
            f"Join link: {config.JOIN_LINK}\n{period.upper()} report stats: {json.dumps(facts)}\nContext (30-day) stats: {json.dumps(facts30)}\n\n"
            f"This is the {period} report" + (" (a whole year: celebrate the milestone, stay humble)" if period == "yearly" else "") + ". "
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
            c = _fallback(today, month, period)
    tags = " ".join(dict.fromkeys(c.get("hashtags") or BASE_TAGS))
    c["telegram"] = f"{c['telegram']}\n\n{tags}\n\n{DISCLAIMER}"
    c["tags"] = tags
    c["x_tags"] = " ".join(list(dict.fromkeys(c.get("hashtags") or BASE_TAGS))[:3])
    return c
