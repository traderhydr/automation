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

## Update – user links supplied
- Defaults set in config: free channel https://t.me/ZoroTradez, X https://x.com/Trader_Hydr, YouTube https://youtube.com/@traderhydr (stripped ?si= share tracking), BloFin https://partner.blofin.com/d/HYDR, Binance creator link (kept as given). PUBLIC_CHANNEL should be @ZoroTradez (bot must be admin).
- Copy trading link set (BloFin copy-trade profile 50803037201). STILL MISSING: PREMIUM_LINK, CONTACT_LINK, RANDOM_SECRET, real trade samples, keys. CHANNEL_NAME unconfirmed (examples used SABBOT / signal template says 'SABBOT REAL'; handles are Trader_Hydr / ZoroTradez).

## Update – premium = DM
- Premium joining is by DM: PREMIUM_LINK/CONTACT_LINK = https://t.me/Hydrzoro, handle @Hydrzoro (user personally replies to all queries). Link block says 'Join Premium: DM @Hydrzoro'; signal captions: 'DM @Hydrzoro to join'. Contact line is hidden when identical to premium.
- STILL MISSING: RANDOM_SECRET, CHANNEL_NAME choice, real trade samples, keys.

## Update – branding
- CHANNEL_NAME = 'Trader Hydr' (user), logo = assets/logo.jpg (purple Zoro artwork the user sent; round crop via src/branding.py) on daily grid header, summary card, equity/bars footer, signal chart and scenario chart.
- Fixed config bug: unset GitHub vars arrive as '' and wiped defaults; `env()` now falls back to default on empty.
- Note: logo is third-party anime fan art; may be flagged on X/YouTube ads. STILL MISSING: RANDOM_SECRET, real trade samples, keys.

## Update – real sample #2 (INJ)
- Real final win wording is 'All targets achieved 😎' (NOT 'All take-profit targets achieved'): parser missed it -> fixed in cornix.FINAL. Regression tests in `tests/test_parse.py` (run `python -m unittest discover tests`) cover real posts: all-targets win, trailing-stop close, opposite-direction close (profit and loss), ignored partial/entry posts, signal R:R.
- Final profit already cumulative for the trade (TP3 28.3% -> final 39.8%), so counting only the final post is right.
- Real stop-loss post received & VERIFIED: `#AAVE/USDT Stop Target Hit ⛔ / Loss: 109.0687% 📉` (SHORT, 25X cross; loss can exceed 100% of margin). Also 'All entries achieved' is a harmless partial post. Tests added.

## Update – Cornix CSV export analysed (1,411 signals, 28 Oct-1 Nov 2026, chat 'Botbac')
- 1,348 entered+finished (995W/353L, 73.8% win, avg win +22.9 / avg loss -20.5, raw ROI sum +15,518%, PF 3.14), 50 still open, 13 never entered. ~340 closed trades/day -> tile grid unusable (>40 falls back to summary card). 1 Nov (partial day) was negative: -240% ROI, 38% wins.
- Raw ROI sum across hundreds of trades is NOT an account return (headline '+15517.90%' is misleading): recommend MARGIN_PER_TRADE_PCT / account-return mode. USER HAS NOT YET ANSWERED which to show.
- Added `src/import_csv.py` (backfill) and `main.py --no-fetch`; `HISTORY_PATH` env. CSV not stored in repo. Timezone of CSV Date column unknown (asked/assumed UTC).

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


---
## HANDOFF – end of session 1 (2026-11-01)  <-- READ THIS FIRST TOMORROW

### State of the project
Everything is built, pushed on branch `claude/exciting-ride-xlyjqw`, and tested ONLY on demo / synthetic data and the user's pasted real posts. NOTHING has run against real Telegram, real exchange prices, X, or GitHub Actions. No PR opened. `DRY_RUN=1` by default (nothing posts).
Unit tests: `python -m unittest discover tests` (8 tests, real Cornix post wordings) – all pass.

### What exists (all post types)
1. Daily/weekly/monthly/yearly results reports – calendar periods in GMT+5 (Asia/Karachi), posted just after the period ends (hourly gate 00-02h local, de-dupe in data/posted_reports.json). Daily card = tile grid (<=40 trades) else summary card. Free-sample trades get a gold star; losses always shown.
2. Signal chart (QNT-style, entry marker + TP/SL + R:R) – only 2 RANDOM signals/day go public, posted IMMEDIATELY (delay setting default 0), caption says "free sample from premium" + DM @Hydrzoro. Teasers logged in data/teasers.json.
3. BTC support/resistance "bounce vs dump" scenario chart (`--scenario BTCUSDT`), daily workflow.
4. Links block under every post (free channel, X, YouTube, copy trading, BloFin ref, Binance creator, premium = DM @Hydrzoro) + auto referral disclosure.
5. Branding: "Trader Hydr" + round logo assets/logo.jpg.
6. CSV backfill: `python -m src.import_csv export.csv --tz UTC --until DATE`; `main.py --no-fetch` builds reports from saved history.

### User facts
- Telegram free channel https://t.me/ZoroTradez (PUBLIC_CHANNEL=@ZoroTradez, bot must be admin); premium joined by DM @Hydrzoro; X @Trader_Hydr; YouTube @traderhydr; GitHub repo traderhydr/automation.
- Private channel is PAID. Signals: own "SABBOT REAL" template + Cornix bot updates. Verified wordings: `All targets achieved 😎` (win), `Stop Target Hit ⛔ / Loss: 109.07%` (stop), `Closed at trailing stoploss after reaching take profit`, `Closed due to opposite direction signal`. Leverage 15x/25x cross; losses can exceed 100% of margin.
- Cornix CSV export analysed: 1,348 finished trades in 4 days (~340/day), 73.8% wins, PF 3.14, raw ROI sum +15,518%; 1 Nov partial day was negative (38% wins).

### OPEN QUESTIONS (ask user first thing)
1. Headline number: raw per-trade ROI sum (+15,518% looks misleading) vs ACCOUNT RETURN (`MARGIN_PER_TRADE_PCT`, e.g. 1-2% margin/trade) – what % of account does each trade use? Recommended: account return.
2. Time zone of the CSV Date column (assumed UTC). Is the CSV the same stream as the public posts (chat "Botbac")?
3. Daily card at ~340 trades/day: build compact version (counts + top winners/losers)?
4. Logo is third-party anime fan art (Zoro) – OK, or make an original Trader Hydr logo?

### USER STILL MUST PROVIDE / DO (secrets go in GitHub secrets, never in chat)
- `TG_API_ID`, `TG_API_HASH`, `TG_SESSION_STRING` (run `python -m src.make_session` locally once), `PRIVATE_CHANNEL`
- `TG_BOT_TOKEN` (BotFather), `PUBLIC_CHANNEL=@ZoroTradez` (bot = admin there)
- `ANTHROPIC_API_KEY` (optional: AI captions; template fallback works without)
- X keys (`X_API_KEY/SECRET`, `X_ACCESS_TOKEN/SECRET`; app needs Read+Write; free tier may block image upload -> text-only fallback)
- `RANDOM_SECRET` (any random text, GitHub secret) – keeps daily random teaser times unpredictable
- optional: `DISCORD_WEBHOOK_URL`, `MARGIN_PER_TRADE_PCT`, `assets/hero.jpg`
- Repo should be PRIVATE (trade history is committed by the workflows).

### Known risks / TODO next session
- First real dry run: `DRY_RUN=1 python main.py --period daily` + `--signals --hours 6` + `--scenario BTCUSDT` on a machine with network; check live candle fetch (Binance->Bybit->OKX->Gate, Binance blocks US IPs incl. GitHub runners), chart levels, caption lengths, then set DRY_RUN=0.
- GitHub Actions: signals.yml runs every 10 min (may exceed free minutes on private repos; consider small VPS loop). Scheduled runs can be delayed; reports catch up within 3h.
- Teaser<->trade matching is best-effort (coin + time, <=14 days) because Cornix close posts carry no signal id.
- Mistake fixed: .gitignore was accidentally emptied; restored. Generated images/caches untracked (history still has demo images + 3 aggregate charts from the real CSV).
- Legal/ToS: finance & crypto promotion rules, X/Meta ad policies; every post carries risk disclaimer; referral links carry disclosure.

- 2026-11-02: user now HAS Telegram API ID + hash (not shared in chat, correctly). Next: make_session -> TG_SESSION_STRING, `src/list_channels.py` (added) to find PRIVATE_CHANNEL id, then add 4 GitHub secrets, then first real DRY_RUN.

- Private channel title = 'zoro gem trades' -> PRIVATE_CHANNEL=zoro gem trades (fetch.py now resolves by title; falls back to 'contains'; errors if ambiguous). Untested against real Telegram.

- 2026-11-02: user runs on Debian server (venv at ~/automation/.venv). First run failed 'Incorrect padding' = session string corrupted by copy/paste. make_session now writes TG_SESSION_STRING directly into .env (chmod 600). User given equivalent heredoc to run on the server.

- 2026-11-02 (user's server): FIRST REAL RUN WORKED. Session saved, channel resolved by title, 48 closed trades parsed for 2 Nov: 39 wins/9 losses, total -286.39% (30-day ctx -721%, 55.6% win rate) => the channel's real numbers are much weaker than the CSV's (+15,518% over 4 days) and the CSV has ~340 trades/day vs 48 in channel => CSV (chat 'Botbac') is a DIFFERENT/bigger stream. MUST ask which stream is the public record. Added `--preview` (sends result to user's Saved Messages) and `python -m src.breakdown [date]` (worst/best trades, by-day). User had several stray Telegram sessions; told to keep newest only.

- 2026-11-02 evening: `python -m src.breakdown 2026-11-02` on real history: 48 trades, 39W (avg +14.3%) / 9L (avg -93.8%): five losses ~ -110% (JUP, TAO, WLD, STRK, POL), LINK -90.9, three ~ -66. By day (GMT+5): 10-31 445 trades +556.5%; 11-01 334 trades -991.5%; 11-02 48 trades -286.4%. Break-even needs ~87% win rate at this win/loss size.
- UNRESOLVED: channel vs CSV disagree on Oct 31 totals (channel +556% vs CSV(PKT) +2685%, but counts 445 vs 442). Same AAVE SHORT stop-out: channel -109.07 vs CSV -108.56 -> CSV is probably the user's own Cornix account, channel = signal-level; they may legitimately differ. Added `src/show_raw.py` (raw posts per coin) so we can verify a losing trade's full post sequence. Waiting for user to run it for JUP and paste.

- 2026-11-02: USER'S CAPTION TEMPLATE adopted for all result reports (src/caption.py `telegram_report`, `links.ecosystem_block`): '📊 DAILY PERFORMANCE REPORT · date', intro line, '⚡ THE BREAKDOWN' bullets, '🌐 OFFICIAL ECOSYSTEM & LINKS' (VIP & Signals / Execution & Copy Trading / Media & Socials), ━━━ separators. Changes I made for accuracy: 'hit targets' -> 'in profit'; '30-Day' label = actual days tracked (e.g. '3-Day'); kept referral disclosure + risk disclaimer + hashtags below. Telegram text is now always this template (exact numbers); Claude only writes X text/hashtags. Signals/scenario posts still use the compact link list. User received first --preview in Saved Messages (works).

- 2026-11-02 JUP CHECK DONE (real posts via show_raw): the -111.41% JUP loss is REAL: LONG signal 11-01 22:35 (25x, SL 0.24567; Entry 3 filled 11-02 17:35) -> `Stop Target Hit ⛔ Loss: 111.4061%` at 22:24 PKT 11-02; parser counted it once, correctly. Parser verified on real sequences (multiple concurrent signals per coin = separate trades, each closes once; TP posts ignored; trailing/opposite closes counted).
- KNOWN MINOR: trade `side` is a best-effort guess (symbol->side from signals in fetch window) and can be wrong when a coin has LONG and SHORT signals in the same window (JUP loss labelled SHORT though it was the LONG). Side is not used in any public output.
- STRUCTURAL FACT for honesty: 25x leverage => ~4% adverse move = 100% of margin; signal SLs are ~5% away => every stop-out costs >100% margin (-110% typical). Avg win +14%, avg loss -94% => needs ~87% win rate to break even.
- New caption template preview reached user's Saved Messages OK. Win-rate rounding now half-up.

- 2026-11-02: user HAS bot token + channel id (not shared in chat). Added `python -m src.check_bot` (verifies bot, channel, admin + post right; posts nothing; mock-tested). PUBLIC_CHANNEL may be @username or numeric -100... id. Next: user adds TG_BOT_TOKEN/PUBLIC_CHANNEL to .env, runs check_bot, then first controlled live post only after headline decision (raw ROI vs account return).

- 2026-11-02: user has THREE channels: 2 public + 1 private (private = paid 'zoro gem trades' source). Multi-channel posting built: PUBLIC_CHANNEL accepts comma list; optional routing CHANNELS_REPORTS / CHANNELS_SIGNALS / CHANNELS_OUTLOOK (default: all public channels get everything). check_bot checks every channel. ASK USER which channel gets which content (and whether the private/premium channel should also receive reports). SAFETY: every bot post carries an invisible marker (publish.MARK) and fetch/parse skip marked messages, because a signal caption ('LONG', '5.12%') WAS parsed as a fake trade in a test.

- 2026-11-02: user wants the SAME posts in EVERY channel (2 public + 1 private-but-FREE channel with more active members; separate from the PAID source channel 'zoro gem trades'). So no routing overrides: PUBLIC_CHANNEL=@pub1,@pub2,-100<private id>. Delivery is now per-channel with per-channel de-dupe (reports: posted_reports.json keys 'period:date|chat'; signals: done_chats in public_signals.json), one failing channel never blocks others, Discord/X only once. Mock-tested. Need user to confirm the paid source channel is NOT one of the 3 targets.

- 2026-11-02: LIVE CANDLE FETCH WORKS from the user's server (real BTC data in `--scenario BTCUSDT --preview`). Server font lacks the Bitcoin glyph (U+20BF) -> header now uses plain letter. Scenario + signal captions moved to the same clean template as the report (`caption.clean_post`: separators, spacing, grouped ecosystem links, disclosure). Next: user checks preview image, then ONE controlled live post: `DRY_RUN=0 python main.py --scenario BTCUSDT`. Still pending: headline decision (raw ROI vs account return), cron on server, X keys.

- 2026-11-02: FIRST LIVE POST DONE: BTC outlook chart posted to all 3 channels via `DRY_RUN=0 python main.py --scenario BTCUSDT` (user confirmed). User DECIDED: headline = ACCOUNT RETURN (not raw ROI); wants automation of: BTC outlook daily, free sample signals, results reports (via cron on their Debian server). Built scripts/ (run_signals.sh every 5 min, gate_outlook.sh, gate_reports.sh, install_cron.sh) + guard: reports refuse to post while MARGIN_PER_TRADE_PCT>=100 (override ALLOW_RAW_ROI=1). WAITING ON USER: MARGIN_PER_TRADE_PCT value (what % of account each trade uses), then they run ./scripts/install_cron.sh. Not yet verified on the server: cron + scripts, signal selection against real signals, report posting. X keys still not set.

- 2026-11-02: user trades with 3% margin per trade -> set MARGIN_PER_TRADE_PCT=3 (already in their .env). Real-data check: with 3% per signal, daily results would be Oct31 +16.7%, Nov1 -29.7%, Nov2 -8.6% (3-day -21.6%). BUT CSV shows up to 123 trades open at once (avg 77 on Oct 31) => 3% each needs ~370% of an account's margin: figure is a MODEL (every signal traded), not a real account result. PNL_NOTE now reads 'Model return at 3% margin per signal'. ASK USER: does Cornix really trade every signal / is there a max-open-trades limit? Real verifiable stat = their BloFin copy-trading profile ROI. User's cron install not yet confirmed.

- 2026-11-02: USER INSTALLED CRON on the server (signals every 5 min, outlook gate hourly :15, reports gate hourly :10). Added freshness guard: free samples only from signals <= PUBLIC_SIGNAL_MAX_AGE_MIN (30) old (a passed slot could otherwise grab a 4h-old signal). Next: confirm logs/signals.log shows slot lines; first daily report ~00:10 PKT; user still to answer: does Cornix trade every signal / max open trades? BloFin copy-trade ROI as verifiable stat.
