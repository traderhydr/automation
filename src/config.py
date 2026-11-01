import os
from dotenv import load_dotenv

load_dotenv()

def env(name, default=""):
    return os.getenv(name, default).strip()

TG_API_ID = int(env("TG_API_ID", "0") or 0)
TG_API_HASH = env("TG_API_HASH")
TG_SESSION_STRING = env("TG_SESSION_STRING")
PRIVATE_CHANNEL = env("PRIVATE_CHANNEL")
TG_BOT_TOKEN = env("TG_BOT_TOKEN")
PUBLIC_CHANNEL = env("PUBLIC_CHANNEL")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
CLAUDE_MODEL = env("CLAUDE_MODEL", "claude-sonnet-5-5")
DISCORD_WEBHOOK_URL = env("DISCORD_WEBHOOK_URL")
CHANNEL_NAME = env("CHANNEL_NAME", "My Trading Signals")
JOIN_LINK = env("JOIN_LINK")
TIMEZONE = env("TIMEZONE", "UTC")
DRY_RUN = env("DRY_RUN", "1") == "1"
