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
# Cornix % are ROI on each trade's own margin (already x leverage). If each trade uses e.g. 2% of your account,
# set MARGIN_PER_TRADE_PCT=2 so reports show ACCOUNT return (sum of roi * 2%). 100 = report raw per-trade ROI.
MARGIN_PER_TRADE_PCT = float(env("MARGIN_PER_TRADE_PCT", "100") or 100)
PNL_NOTE = env("PNL_NOTE", "Leveraged ROI on margin" if MARGIN_PER_TRADE_PCT == 100 else
               f"Account return, {MARGIN_PER_TRADE_PCT:g}% margin/trade")
HERO_IMAGE = env("HERO_IMAGE", "assets/hero.jpg")      # optional brand photo shown on the right of the results card
LEVERAGE_NOTE = env("LEVERAGE_NOTE", "Leveraged returns")  # e.g. "Returns with 10x-25x leverage"
EXECUTION_NOTE = env("EXECUTION_NOTE", "Executed via Cornix")
