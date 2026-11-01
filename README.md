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

## Report periods & X (Twitter)
`python main.py --period daily|weekly|monthly|yearly` — rolling windows of 1 / 7 / 30 / 365 days. Yearly bar charts are per month.
The workflow runs daily (Mon–Fri), weekly (Sat), monthly (1st) and yearly (1 Jan); use *Run workflow* to trigger any period by hand.
Weekly/monthly/yearly use the saved `data/trades.json` history, so they only get as long as the history you have collected.

**X setup:** create an app at developer.x.com, set permissions to *Read and Write*, generate the access token/secret (after changing permissions), and fill `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`. Posts are ≤280 chars with 3 hashtags and up to 4 images. The free API tier may block image upload; the code then falls back to a text-only post.

## Cornix
`src/cornix.py` reads the updates the Cornix bot posts in your channel. A trade is counted **once**, when it reaches a final state
(`All take-profit targets achieved`, `Stop Target Hit`, `Closed due to ...`) using the `Profit:` / `Loss:` % Cornix shows.
Intermediate `Take-Profit target N` and entry messages are ignored. Cornix % normally already includes leverage, so label your posts accordingly.
Your own signal template (`Pair:` / `Direction:`) is recognised for the long/short side, and closes such as `Closed at trailing stoploss after reaching take profit` and `Closed due to opposite direction signal` count as final results.
**Leverage:** with 25x, per-trade ROI can be +20% while the account moves a fraction of that, and adding ROIs overstates account growth. Set `MARGIN_PER_TRADE_PCT` (e.g. `2`) to report account return; charts print the basis in the footer.
Trades are de-duplicated by Telegram message id, so overlapping daily/weekly runs never double count.

## Trade message format (non-Cornix)
Closed-trade messages like `#BTCUSDT LONG closed ✅ +3.2%`, `ETH/USDT short SL hit -1.5%`, `XAUUSD BUY TP2 +1.8R` parse by regex.
Other formats fall back to Claude. Adjust `src/parse.py` to match your real posts.

## Important
- Charts use only your real posted results; the `--demo` data is fake and is never posted.
- Posts carry a risk disclaimer. Promoting signals/paid groups with performance claims is regulated in many countries (e.g. SEBI in India, SEC/FCA elsewhere) and X/Meta ads have crypto/finance rules — check yours. Never imply guaranteed profit.
- Percent results ignore position size/fees; state your method if you quote returns.
