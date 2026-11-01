"""Run once locally: logs into your Telegram account and prints a session string
to put in TG_SESSION_STRING (so the daily job can run headless)."""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from . import config

with TelegramClient(StringSession(), config.TG_API_ID, config.TG_API_HASH) as c:
    print("\nTG_SESSION_STRING=" + c.session.save())
