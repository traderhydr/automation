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

## Your links (shown under every post)
Set as repo **variables** (or `.env`): `TELEGRAM_LINK` (free channel), `PREMIUM_LINK` (premium channel / how to join), `CONTACT_LINK` (your DM), `X_LINK`, `BLOFIN_REF_LINK`, `COPY_TRADING_LINK`, `BINANCE_CREATOR_LINK`. Blank ones are skipped.
Referral/affiliate links automatically get a "I may earn a commission" disclosure line (required by most platforms and regulators). On X the links go in a reply under the post to keep the main post clean.
Don't paste your private channel's open invite link anywhere public – use a join-request link or a payment/bot link so only paying members get in. Long captions (>1024 chars) are sent as a message right after the photo so nothing is cut off.

## Honesty rules for reports
- Every report uses **all** closed trades, wins and losses (never only the teasers); cards and captions say "losses included".
- The free sample signals (the 2 random ones posted each day) are **highlighted** in the results: a gold ★ outline on their tile in the daily grid, plus a line like `★ Free samples shared with you: OP +19.73% · BTC -44.01% · 1 still open`. Losing samples are shown exactly like winning ones.
- Weekly/monthly/yearly cards show the samples' running tally (`★ Free samples: 31W / 9L`) over the whole period; teasers are logged permanently in `data/teasers.json`.
- A teaser's result is matched to the first close of the same coin after the signal (Cornix close posts have no signal id), so overlapping trades on one coin can be mismatched — rare, but worth knowing.

## Report periods & X (Twitter)
**Schedule (calendar periods, in your `TIMEZONE`):** daily report when the day ends; weekly when Sunday ends (Mon–Sun week); monthly when the month's last day ends; yearly when 31 Dec ends. The workflow checks hourly and posts in the first window after local midnight (00:00–02:59, catches up if GitHub skipped a run); `data/posted_reports.json` prevents duplicates. Manual run for any date: `python main.py --period weekly --date 2026-11-01` (add `--force` to repost). Set repo variable `TIMEZONE` (e.g. `Asia/Kolkata`; default UTC).

(Older text below mentions rolling windows – superseded by the above.)

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

## Signal charts (QNT-style) – free-channel samples, `python main.py --signals`
Your private channel is paid, so the public channel only gets a **teaser**: `PUBLIC_SIGNALS_PER_DAY` (default **2**) random signals per day,
each posted **immediately** (`PUBLIC_SIGNAL_DELAY_MIN=0`) so people can try it live; set e.g. `30` to delay free posts after the premium post.
- **Random picks:** each day N random times are drawn between `PUBLIC_WINDOW_START`–`END` (08:00–22:00, ≥90 min apart, seeded by `RANDOM_SECRET`); the first new signal after each time is the pick. Not cherry-picked, so wins and losses both show.
- **Chart:** candles up to the moment of posting, entry marker ("OPENED HERE" when Cornix reported the fill), entries, TP1-n, SL and the **R:R** (reward to each TP ÷ distance Entry 1 → SL).
- **Caption:** levels + R:R + honest **status so far** (open / TPn reached / stopped out) + "free sample from our premium channel" (or the delay note if a delay is set) + `PREMIUM_LINK`.
- State in `data/public_signals.json` (slots, picked signals) so nothing is posted twice. `PUBLIC_SIGNALS_PER_DAY=0` = every signal, still delayed.
- Candles: Binance → Bybit → OKX → Gate (Binance blocks US IPs like GitHub runners). Scale mismatches (1000PEPE…) are fixed or the signal is skipped.
- `.github/workflows/signals.yml` runs every 10 min (GitHub may delay it); `python main.py --signals --demo` renders a sample.

## Market outlook chart (bounce vs dump) – `python main.py --scenario BTCUSDT,ETHUSDT`
Candles (1h) → swing highs/lows → clustered into **resistance**, a **support zone** and a **major support**; 24h change/high/low/volume are computed from the candles.
The chart shows both scenarios (bounce toward resistance / dump toward major support) with a "Key Level in Focus" note whose wording adapts to whether price is above, inside or below the zone.
Captions say plainly that levels are algorithmic scenarios, not predictions. `.github/workflows/outlook.yml` posts daily (05:15 UTC; set repo variable `OUTLOOK_SYMBOLS`).

## Trade message format (non-Cornix)
Closed-trade messages like `#BTCUSDT LONG closed ✅ +3.2%`, `ETH/USDT short SL hit -1.5%`, `XAUUSD BUY TP2 +1.8R` parse by regex.
Other formats fall back to Claude. Adjust `src/parse.py` to match your real posts.

## Important
- Charts use only your real posted results; the `--demo` data is fake and is never posted.
- Posts carry a risk disclaimer. Promoting signals/paid groups with performance claims is regulated in many countries (e.g. SEBI in India, SEC/FCA elsewhere) and X/Meta ads have crypto/finance rules — check yours. Never imply guaranteed profit.
- Percent results ignore position size/fees; state your method if you quote returns.
