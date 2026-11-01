"""Your contact / referral links, appended to every post. Blank ones are skipped."""
import html
from . import config

# (label, emoji, config value, is_affiliate)
def _items():
    return [
        ("Free channel", "📢", config.TELEGRAM_LINK, False),
        ("Contact / DM", "💬", "" if config.CONTACT_LINK == config.PREMIUM_LINK else config.CONTACT_LINK, False),
        ("X (Twitter)", "🐦", config.X_LINK, False),
        ("YouTube", "▶️", config.YOUTUBE_LINK, False),
        ("Copy trading", "🤝", config.COPY_TRADING_LINK, True),
        ("BloFin (referral)", "📈", config.BLOFIN_REF_LINK, True),
        ("Binance (creator)", "🟡", config.BINANCE_CREATOR_LINK, True),
    ]


def _clean(u):
    return u if u.startswith(("http://", "https://")) else ""


def telegram_block():
    """HTML block for Telegram captions / messages."""
    rows, aff = [], False
    for label, emoji, url, is_aff in _items():
        if _clean(url):
            rows.append(f'{emoji} {label}: {html.escape(url, quote=False)}')
            aff = aff or is_aff
    if config.PREMIUM_LINK and _clean(config.PREMIUM_LINK):
        rows.insert(0, f"💎 Join Premium: DM {config.PREMIUM_HANDLE} → {html.escape(config.PREMIUM_LINK, quote=False)}")
    if not rows:
        return ""
    note = "\n<i>Referral / affiliate links: I may earn a commission at no extra cost to you.</i>" if aff else ""
    return "🔗 <b>Links</b>\n" + "\n".join(rows) + note


def plain_block():
    """Plain-text version (X reply, Discord)."""
    rows, aff = [], False
    for label, emoji, url, is_aff in _items():
        if _clean(url):
            rows.append(f"{emoji} {label}: {url}"); aff = aff or is_aff
    if config.PREMIUM_LINK and _clean(config.PREMIUM_LINK):
        rows.insert(0, f"💎 Join Premium: DM {config.PREMIUM_HANDLE} → {config.PREMIUM_LINK}")
    if not rows:
        return ""
    return "🔗 Links\n" + "\n".join(rows) + ("\n(Referral/affiliate links – I may earn a commission.)" if aff else "")
