# Trade report automation

Private Telegram channel → parse closed trades → stats → charts → AI captions → post to your public channel (+ Discord / X).

```
fetch.py (Telethon)  →  parse.py (regex + Claude fallback)  →  stats.py  →  charts.py  →  caption.py (Claude)  →  publish.py
```

## Setup
1. `pip install -r requirements.txt`, copy `.env.example` → `.env`.
2. Get `TG_API_ID` / `TG_API_HASH` at https://my.telegram.org, then run `python -m src.make_session` once and paste the string into `TG_SESSION_STRING`. (Your own account must be a member of the private channel.)
3. Create a bot with @BotFather, add it as **admin** of your public channel, set `TG_BOT_TOKEN` and `PUBLIC_CHANNEL`.
4. Try it: `python main.py --demo` (fake data, writes images to `out/`, posts nothing).
5. Real dry run: `python main.py` with `DRY_RUN=1`. When happy, set `DRY_RUN=0`.
6. Schedule: add the same values as GitHub repo **secrets** (and `CHANNEL_NAME`, `JOIN_LINK`, `DRY_RUN` as **variables**); `.github/workflows/daily.yml` runs it every weekday.

## Trade message format
Closed-trade messages like `#BTCUSDT LONG closed ✅ +3.2%`, `ETH/USDT short SL hit -1.5%`, `XAUUSD BUY TP2 +1.8R` parse by regex.
Other formats fall back to Claude. Adjust `src/parse.py` to match your real posts.

## Important
- Charts use only your real posted results; the `--demo` data is fake and is never posted.
- Posts carry a risk disclaimer. Promoting signals/paid groups with performance claims is regulated in many countries (e.g. SEBI in India, SEC/FCA elsewhere) and X/Meta ads have crypto/finance rules — check yours. Never imply guaranteed profit.
- Percent results ignore position size/fees; state your method if you quote returns.
