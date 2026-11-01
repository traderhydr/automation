"""Pull the last N hours of messages from the private channel."""
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from . import config


async def _fetch(hours):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    chan = config.PRIVATE_CHANNEL
    chan = int(chan) if chan.lstrip("-").isdigit() else chan
    out = []
    async with TelegramClient(StringSession(config.TG_SESSION_STRING),
                              config.TG_API_ID, config.TG_API_HASH) as c:
        async for m in c.iter_messages(chan, offset_date=None):
            if m.date < since:
                break
            if m.message:
                out.append({"id": m.id, "date": m.date.isoformat(), "text": m.message})
    return list(reversed(out))


def fetch_messages(hours=24):
    return asyncio.run(_fetch(hours))
