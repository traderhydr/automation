# Project memory

## Goal
Automate a daily report from a **private Telegram trades channel**: parse closed trades, compute stats, make charts, generate eye-catching captions + hashtags with Claude, and post to the **public Telegram channel** (optionally Discord / X) to attract members.

## Status (2026-11-01)
- Pipeline built and pushed on branch `claude/exciting-ride-xlyjqw`. No PR opened.
- Only tested with `python main.py --demo` (fake data) and the regex parser on sample messages.
- NOT yet tested: Telegram fetch, Claude captions/fallback parsing, real posting, GitHub Actions workflow.
- `DRY_RUN=1` by default; nothing is posted until set to `0`.

## Layout
- `main.py` – pipeline entry (`--demo`, `--hours N`)
- `src/fetch.py` – Telethon read of private channel (user session)
- `src/parse.py` – regex parser + Claude fallback → `{date, symbol, side, pnl_pct}`
- `src/stats.py` – P&L, win rate, profit factor, drawdown, equity, daily
- `src/charts.py` – summary card, equity curve, daily bars (matplotlib, dark theme)
- `src/caption.py` – Claude-written Telegram/X captions + hashtags (template fallback)
- `src/publish.py` – Telegram bot, Discord webhook, X (tweepy)
- `src/make_session.py` – one-time Telegram session string generator
- `.github/workflows/daily.yml` – weekday cron, persists `data/trades.json`
- `.env.example`, `README.md`

## Update – periods + X
- Added `--period daily|weekly|monthly|yearly` (`src/periods.py`), period-aware charts/captions, X posting (3 hashtags, 4 images, text-only fallback), and workflow schedules for all four periods.
- Verified only with `--demo` for all periods; X posting untested (needs keys; free tier may block media).
- History starts empty on a fresh install, so longer reports need time (or a backfill: `python main.py --hours 8760` once).

## Update – Cornix
- User's channel contains **Cornix** bot updates. Added `src/cornix.py` (final-state-only counting, side from signal post, dedupe by message id). Tested only on self-written samples in the remembered Cornix layout – NOT on real messages. Need real samples to confirm wording (esp. single-TP trades, partial TP then stop, leverage in %).

## Update – real samples (SABBOT REAL)
- User pasted real posts: custom signal template (`Pair:`/`Direction:`/`Leverage: Cross 25X`) + Cornix updates (Entry n, Take-Profit target n, `Closed at trailing stoploss after reaching take profit`, `Closed due to opposite direction signal`, `Stop Target Hit` assumed). Parser updated and verified on these; counts only final closes (trades still open / only partial TP are excluded).
- Leverage 25x: added `MARGIN_PER_TRADE_PCT` + `PNL_NOTE` (chart footer). ASK USER what % of account each trade uses.
- Channel branding: `CHANNEL_NAME=SABBOT`.

## Update – signal charts
- User wants QNT-style signal chart posted PUBLICLY (shows where trade opened + R:R). Built `src/signals.py`, `src/signal_chart.py`, `main.py --signals`, `.github/workflows/signals.yml`.
- R:R = reward to each TP / distance Entry1→SL (ORDI sample: TP1 0.12R … TP4 1.1R, risk 5.12%). Candle APIs unreachable from the dev sandbox -> only parsers mocked + chart tested on synthetic candles; live fetch UNTESTED.
- Still to do: BTC support/resistance scenario chart (reference #2) not built; confirm with user whether signals should be delayed (paid members).

## Update – BTC scenario chart
- Built `src/scenario.py` (pivot clustering -> resistance / support zone / major support, 24h stats), `src/scenario_chart.py`, `main.py --scenario SYMBOLS`, `.github/workflows/outlook.yml`. All 3 user reference post types now exist (daily results grid, signal chart, scenario chart).
- Tested on synthetic candles only (exchange APIs blocked in sandbox). Levels are heuristic; wording is conditional, not predictive.
- Next: real-data dry run by user; decide signal delay for paid members; update docs/tune styles after seeing real output.

## Update – calendar schedule
- Reports now cover CALENDAR periods in `TIMEZONE` (day / Mon-Sun week / month / year), posted right after the period ends: hourly workflow gate (00-02h local) in `.github/workflows/daily.yml`, de-dupe via `data/posted_reports.json`, `--date`/`--force` flags. Gate logic verified with simulated dates; real Actions run untested.
- TIMEZONE = GMT+5 -> `Asia/Karachi` (user said 'gmt' then '+5'; ASSUMED Pakistan-style UTC+5, no DST). Now the default in config + workflow. Reports run 00:00-24:00 GMT+5, post ~00:10 local = 19:10 UTC. Confirm with user if they are elsewhere on +5. Note: signals workflow every 10 min can exceed GitHub free minutes on private repos.

## Update – paid channel teaser policy
- Private channel is PAID. Public/free channel gets only 2 RANDOM signals/day (`PUBLIC_SIGNALS_PER_DAY`), posted 30 min after the premium post (`PUBLIC_SIGNAL_DELAY_MIN`), random times drawn per day in 08-22 local (`src/public_signals.py`, state `data/public_signals.json`). Caption shows honest status + premium CTA. Replaced the old 'post every signal immediately' behaviour.
- Simulated a full day of runs: exactly 2 posts/day, >=30 min delay. Real run untested.
- User must set: PREMIUM_LINK, RANDOM_SECRET (GitHub secret). Results reports (daily etc.) still use ALL trades (not only the 2 teasers) – ask user if that is what they want publicly.

## Update – free samples are IMMEDIATE
- User decision: the 2 random free signals/day post IMMEDIATELY (no delay) so members can try them live. `PUBLIC_SIGNAL_DELAY_MIN` default is now 0 (still configurable). Caption says 'free sample from our premium channel' + PREMIUM_LINK. Supersedes the 30-min delay in the previous update.

## Update – honesty / teaser highlight
- User: reports include ALL trades, losses included, and HIGHLIGHT the 2 free teaser trades (honesty). Implemented: `data/teasers.json` permanent log (`public_signals.log_teaser`), `mark_teasers` best-effort coin+time matching (<=14d), gold star tile + footer line on daily grid, tally on other cards, caption line, 'still open' count. Tested on reference 25-trade day with a losing teaser.

## Update – links
- `src/links.py`: link block under every post (Telegram HTML; plain for Discord / X reply). Vars: TELEGRAM_LINK (free channel), PREMIUM_LINK, CONTACT_LINK, X_LINK, BLOFIN_REF_LINK, COPY_TRADING_LINK, BINANCE_CREATOR_LINK (all blank until user supplies). Affiliate disclosure auto-added. Telegram photo captions >1024 chars now sent as follow-up message.

## Decisions / assumptions
- Trade format is **assumed** (e.g. `#BTCUSDT LONG closed ✅ +3.2%`, `+1.8R` with 1R = 1%). Needs adjusting to the user's real messages.
- Results are in % (no position sizing/fees).
- Model: `claude-sonnet-5-5` (configurable via `CLAUDE_MODEL`).
- Captions use only real numbers; disclaimer appended to every post; prompt forbids guarantees/"risk-free".
- Demo data is fake and never posted.

## Open items / next steps
1. Get real sample messages from the user and tune `src/parse.py`.
2. User sets up Telegram API keys, session string, bot as admin of public channel, GitHub secrets/variables.
3. Run a real dry run, review output, then set `DRY_RUN=0`.
4. Possible additions: Instagram/LinkedIn image sizes, weekly/monthly recap, per-symbol charts.
5. Reminder to user: finance/crypto promotion rules (SEBI/SEC/FCA, platform ad policies) – check local regulations.
