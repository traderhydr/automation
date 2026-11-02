"""Run once: logs into your Telegram account and SAVES the session string straight into .env
(no copy/paste - long strings often get broken by terminals).   python -m src.make_session"""
import pathlib
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from . import config

with TelegramClient(StringSession(), config.TG_API_ID, config.TG_API_HASH) as c:
    s = c.session.save()
env = pathlib.Path(".env")
lines = [l for l in env.read_text().splitlines() if not l.startswith("TG_SESSION_STRING=")] if env.exists() else []
lines.append("TG_SESSION_STRING=" + s)
env.write_text("\n".join(lines) + "\n")
env.chmod(0o600)
print(f"\nSaved TG_SESSION_STRING to .env (length {len(s)}). Treat it like a password – never share it.")
