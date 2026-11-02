"""Prints the channels/groups your Telegram account can see, with the id to use as PRIVATE_CHANNEL.
Run after make_session:  python -m src.list_channels"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from . import config


async def main():
    async with TelegramClient(StringSession(config.TG_SESSION_STRING), config.TG_API_ID, config.TG_API_HASH) as c:
        print(f"{'ID (use this)':<18} {'Type':<9} Title")
        async for d in c.iter_dialogs():
            if d.is_channel or d.is_group:
                kind = "channel" if getattr(d.entity, "broadcast", False) else "group"
                print(f"{d.id:<18} {kind:<9} {d.name}")

asyncio.run(main())
