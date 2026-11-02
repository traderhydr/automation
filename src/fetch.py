"""Pull the last N hours of messages from the private channel."""
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from . import config
from .publish import is_own_post


async def _resolve(client, ref):
    """PRIVATE_CHANNEL can be a numeric id (-100...), an @username, or just the channel's TITLE (e.g. 'zoro gem trades')."""
    if ref.lstrip("-").isdigit():
        return int(ref)
    if ref.startswith("@") or ref.startswith("https://t.me/"):
        return ref
    want = ref.casefold().strip()
    matches = []
    async for d in client.iter_dialogs():
        if (d.is_channel or d.is_group) and d.name.casefold().strip() == want:
            matches.append(d)
    if not matches:       # fall back to "contains"
        async for d in client.iter_dialogs():
            if (d.is_channel or d.is_group) and want in d.name.casefold():
                matches.append(d)
    if not matches:
        raise SystemExit(f"No Telegram channel/group titled '{ref}' found for this account. Run: python -m src.list_channels")
    if len(matches) > 1:
        names = ", ".join(f"{m.name} ({m.id})" for m in matches)
        raise SystemExit(f"'{ref}' matches several chats: {names}. Set PRIVATE_CHANNEL to the numeric id instead.")
    return matches[0].entity


async def _fetch(hours):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    chan = config.PRIVATE_CHANNEL
    out = []
    async with TelegramClient(StringSession(config.TG_SESSION_STRING),
                              config.TG_API_ID, config.TG_API_HASH) as c:
        chan = await _resolve(c, chan)
        async for m in c.iter_messages(chan, offset_date=None):
            if m.date < since:
                break
            if m.message and not is_own_post(m.message):
                out.append({"id": m.id, "date": m.date.isoformat(), "text": m.message})
    return list(reversed(out))


def fetch_messages(hours=24):
    return asyncio.run(_fetch(hours))
