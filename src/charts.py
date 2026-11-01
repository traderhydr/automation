"""Eye-catching, dark-themed charts built from the real trade data."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import config
from .periods import PERIODS
from . import branding

BG, FG, GREEN, RED, ACC = "#0b1220", "#e8eefc", "#22c55e", "#ef4444", "#38bdf8"


def _style():
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                         "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
                         "axes.edgecolor": "#24324d", "font.size": 12})


def _footer(fig):
    t = fig.text(0.5, 0.012, f"{config.CHANNEL_NAME} • {config.PNL_NOTE} • Past results ≠ future returns • Not financial advice",
                 ha="center", fontsize=9, color="#7f8db0")
    branding.add_logo_before_text(fig, t, size_px=26)


def summary_card(st, ctx, period, path, label=None):
    """Big shareable scoreboard. st = stats for the period, ctx = 30-day stats (used for daily only)."""
    title = PERIODS[period][2] + (f" · {label}" if label else "")
    _style()
    fig = plt.figure(figsize=(8, 8))
    fig.text(0.5, 0.92, config.CHANNEL_NAME.upper(), ha="center", fontsize=20, weight="bold", color=ACC)
    branding.add_logo_fig(fig, 0.05, 0.875, 0.11)
    fig.text(0.5, 0.87, title, ha="center", fontsize=13, color="#9fb0d6")
    col = GREEN if st["total_pct"] >= 0 else RED
    fig.text(0.5, 0.67, f"{st['total_pct']:+.2f}%", ha="center", fontsize=64, weight="bold", color=col)
    fig.text(0.5, 0.60, f"{st['trades']} trades  •  {st['wins']}W / {st['losses']}L  •  "
                        f"{st['win_rate']}% win rate", ha="center", fontsize=14)
    tz = st["teaser"]
    if tz["closed"] or tz["open"]:
        fig.text(0.5, 0.52, f"★ Free samples: {tz['wins']}W / {tz['losses']}L  ({tz['total']:+.1f}%)"
                 + (f"  ·  {tz['open']} still open" if tz["open"] else "") + "  – losses included", ha="center", fontsize=12, color="#f5c22b")
    ref = ctx if period == "daily" else st
    pre = "30-DAY " if period == "daily" else ""
    pf = ref["profit_factor"] if ref["profit_factor"] is not None else "–"
    tiles = [(pre + "P&L", f"{ref['total_pct']:+.1f}%"), (pre + "WIN RATE", f"{ref['win_rate']}%"),
             ("PROFIT FACTOR", f"{pf}"), ("MAX DRAWDOWN", f"-{ref['max_drawdown']}%")]
    for i, (k, v) in enumerate(tiles):
        x = 0.14 + (i % 2) * 0.40
        y = 0.36 - (i // 2) * 0.18
        fig.text(x, y + 0.05, k, fontsize=11, color="#9fb0d6")
        fig.text(x, y, v, fontsize=26, weight="bold")
    _footer(fig)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def equity_curve(st, period, path):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    x = list(range(len(st["days"])))
    ax.plot(x, st["equity"], color=ACC, lw=3)
    ax.fill_between(x, st["equity"], 0, color=ACC, alpha=0.15)
    ax.axhline(0, color="#475569", lw=1)
    step = max(1, len(x) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels([st["days"][i][5:] if period != "yearly" else st["days"][i] for i in x[::step]])
    ax.set_ylabel("Cumulative return (%)")
    ax.set_title(f"Equity curve ({period}):  {st['total_pct']:+.1f}%", fontsize=16, weight="bold", loc="left")
    ax.grid(alpha=0.12)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    _footer(fig)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def bars(st, period, path):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    cols = [GREEN if v >= 0 else RED for v in st["daily"]]
    ax.bar([d[5:] if period != "yearly" else d for d in st["days"]], st["daily"], color=cols)
    ax.axhline(0, color="#475569", lw=1)
    ax.set_title(PERIODS[period][3], fontsize=16, weight="bold", loc="left")
    plt.setp(ax.get_xticklabels(), rotation=60, ha="right", fontsize=9)
    ax.grid(axis="y", alpha=0.12)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    _footer(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def build_all(st, ctx, period, outdir, label=None):
    """Returns image paths. daily: card + 30-day charts; others: card + charts for the period itself."""
    paths = [f"{outdir}/summary.png"]
    if period == "daily" and 0 < st["trades"] <= 40:
        results_grid(st, paths[0], label)
    else:
        summary_card(st, ctx, period, paths[0], label)
    series = ctx if period == "daily" else st
    cpd = "monthly" if period == "daily" else period
    if len(series["days"]) >= 2:
        equity_curve(series, cpd, f"{outdir}/equity.png"); paths.append(f"{outdir}/equity.png")
        bars(series, cpd, f"{outdir}/bars.png"); paths.append(f"{outdir}/bars.png")
    return paths


def results_grid(st, path, date_label=None):
    """Daily-results scoreboard: one tile per closed trade (winners first, losses included)."""
    import os, math
    from datetime import datetime
    import numpy as np
    from matplotlib.patches import FancyBboxPatch
    _style()
    W, H = 1280, 720
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), W, H, color="#15171c"))
    if os.path.exists(config.HERO_IMAGE):       # brand photo: cover the right 40%, fade into the background
        from PIL import Image
        bg = np.empty((H, W, 3), dtype=float); bg[:] = (0x15, 0x17, 0x1c)
        x0 = int(W * 0.60)
        im = Image.open(config.HERO_IMAGE).convert("RGB")
        sc = max((W - x0) / im.width, H / im.height)
        im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1))
        left, top = im.width - (W - x0), (im.height - H) // 2          # crop: keep right edge, centre vertically
        crop = np.asarray(im.crop((left, top, left + (W - x0), top + H)), dtype=float)
        alpha = np.clip(np.linspace(0, 1, W - x0) / 0.45, 0, 1) ** 1.3  # 0 at the seam -> 1
        bg[:, x0:, :] = bg[:, x0:, :] * (1 - alpha[None, :, None]) + crop * alpha[None, :, None]
        ax.imshow(bg.astype("uint8"), extent=(0, W, H, 0), aspect="auto", zorder=1)
    GOLD = "#f5c22b"
    lg = branding.logo_rgba(200)
    hx = 48
    if lg is not None:                       # round logo to the left of the header, like a channel avatar
        ax.imshow(lg, extent=(48, 48 + 56, 28 + 56, 28), zorder=6, aspect="auto"); hx = 48 + 56 + 14
        ax.set_xlim(0, W); ax.set_ylim(H, 0)
    ax.text(hx, 56, f"{config.CHANNEL_NAME.upper()} · {PERIODS['daily'][2]}", color="#f1f3f7", fontsize=17,
            weight="bold", va="center", zorder=5)
    d = date_label or datetime.fromisoformat(st["last"]).strftime("%d %b %Y").upper()
    ax.text(48, 140, d, color=GOLD, fontsize=52, weight="bold", va="center", zorder=5)
    ax.text(48, 226, f"{st['wins']} / {st['trades']} in profit", color="#f1f3f7", fontsize=26,
            weight="bold", va="center", zorder=5)
    tot_col = "#5fd38d" if st["total_pct"] >= 0 else "#f26d6d"
    ax.add_patch(FancyBboxPatch((498, 190), 302, 62, boxstyle="round,pad=0,rounding_size=14",
                                fc="#24272e", ec="none", zorder=4))
    ax.text(516, 221, "TOTAL", color="#9aa1ad", fontsize=14, va="center", zorder=5, weight="bold")
    ax.text(786, 221, f"{st['total_pct']:+.2f}%", color=tot_col, fontsize=25, weight="bold", va="center",
            ha="right", zorder=5)
    items = st["items"]
    cols, gap, x_start, y_start = 5, 10, 48, 276
    cw = (W - 2 * x_start - gap * (cols - 1)) / cols
    rows = math.ceil(len(items) / cols)
    avail = 296
    ch_ = min(50, (avail - gap * (rows - 1)) / rows)
    fs = 15 if ch_ >= 44 else 12
    for i, (sym, v, tz_) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x_start + c * (cw + gap), y_start + r * (ch_ + gap)
        win = v >= 0
        ax.add_patch(FancyBboxPatch((x, y), cw, ch_, boxstyle="round,pad=0,rounding_size=8",
                                    fc=("#23262d" if win else "#3a2423"),
                                    ec=GOLD if tz_ else "none", lw=2.2 if tz_ else 0, alpha=0.93, zorder=4))
        ax.text(x + 12, y + ch_ / 2, ("★ " if tz_ else "") + sym, color="#f1f3f7", fontsize=fs, weight="bold", va="center", zorder=5)
        ax.text(x + cw - 12, y + ch_ / 2, f"{v:+.2f}%", color="#5fd38d" if win else "#f26d6d",
                fontsize=fs, weight="bold", va="center", ha="right", zorder=5)
    if st["first"]:
        f, l = datetime.fromisoformat(st["first"]), datetime.fromisoformat(st["last"])
        ax.text(48, 600, f"Closed trades: {f:%b %d, %H:%M} – {l:%b %d, %H:%M}", color="#8b919c", fontsize=13,
                va="center", zorder=5)
    tz = st["teaser"]
    if tz["closed"] or tz["open"]:
        parts = [f"{s} {v:+.2f}%" for s, v in tz["items"]] + ([f"{tz['open']} still open"] if tz["open"] else [])
        ax.text(48, 628, "★ Free samples shared with you: " + "  ·  ".join(parts) + "  (all trades shown)", color=GOLD, fontsize=12.5,
                weight="bold", va="center", zorder=5)
    ax.text(48, 660, f"Sum of all closed trades, losses included  ·  {config.EXECUTION_NOTE}  ·  {config.LEVERAGE_NOTE}",
            color="#8b919c", fontsize=12.5, va="center", zorder=5)
    ax.text(W - 48, 658, "#DailyResults", color=GOLD, fontsize=13, weight="bold", va="center", ha="right", zorder=6)
    fig.savefig(path, dpi=100)
    plt.close(fig)
