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
