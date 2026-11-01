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
TELEGRAM_LINK = env("TELEGRAM_LINK", "https://t.me/ZoroTradez")          # your public Telegram channel / contact
JOIN_LINK = env("JOIN_LINK") or TELEGRAM_LINK
CONTACT_LINK = env("CONTACT_LINK")            # your Telegram DM / support, e.g. https://t.me/yourusername
X_LINK = env("X_LINK", "https://x.com/Trader_Hydr")
YOUTUBE_LINK = env("YOUTUBE_LINK", "https://youtube.com/@traderhydr")
BLOFIN_REF_LINK = env("BLOFIN_REF_LINK", "https://partner.blofin.com/d/HYDR")
COPY_TRADING_LINK = env("COPY_TRADING_LINK", "https://blofin.com/copy-trade/details/50803037201?module=futures")
BINANCE_CREATOR_LINK = env("BINANCE_CREATOR_LINK", "https://app.binance.com/uni-qr/cpro/ZenithX?l=en&r=VUUMW0NT&uc=app_square_share_link&us=copylink")
TIMEZONE = env("TIMEZONE", "Asia/Karachi")
DRY_RUN = env("DRY_RUN", "1") == "1"
# Cornix % are ROI on each trade's own margin (already x leverage). If each trade uses e.g. 2% of your account,
# set MARGIN_PER_TRADE_PCT=2 so reports show ACCOUNT return (sum of roi * 2%). 100 = report raw per-trade ROI.
MARGIN_PER_TRADE_PCT = float(env("MARGIN_PER_TRADE_PCT", "100") or 100)
PNL_NOTE = env("PNL_NOTE", "Leveraged ROI on margin" if MARGIN_PER_TRADE_PCT == 100 else
               f"Account return, {MARGIN_PER_TRADE_PCT:g}% margin/trade")
HERO_IMAGE = env("HERO_IMAGE", "assets/hero.jpg")      # optional brand photo shown on the right of the results card
LEVERAGE_NOTE = env("LEVERAGE_NOTE", "Leveraged returns")  # e.g. "Returns with 10x-25x leverage"
EXECUTION_NOTE = env("EXECUTION_NOTE", "Executed via Cornix")
SIGNAL_INTERVAL = env("SIGNAL_INTERVAL", "15m")                 # candle size on the signal chart
SIGNAL_MAX_AGE_MIN = int(env("SIGNAL_MAX_AGE_MIN", "45") or 45)  # never post a signal older than this
SCENARIO_INTERVAL = env("SCENARIO_INTERVAL", "1h")
# Free-channel teaser policy (private channel is paid): N random signals/day, posted after a delay.
PUBLIC_SIGNALS_PER_DAY = int(env("PUBLIC_SIGNALS_PER_DAY", "2") or 0)   # 0 = every signal (still delayed)
PUBLIC_SIGNAL_DELAY_MIN = int(env("PUBLIC_SIGNAL_DELAY_MIN", "0") or 0)   # 0 = post immediately (default)
PUBLIC_WINDOW_START = int(env("PUBLIC_WINDOW_START", "8") or 8)         # local hour, inclusive
PUBLIC_WINDOW_END = int(env("PUBLIC_WINDOW_END", "22") or 22)           # local hour, exclusive
PREMIUM_LINK = env("PREMIUM_LINK")                                       # where to subscribe / contact for premium
RANDOM_SECRET = env("RANDOM_SECRET", "change-me")                        # keeps the daily random times unpredictable
