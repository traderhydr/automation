"""Eye-catching, dark-themed charts built from the real trade data."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import config
from .periods import PERIODS

BG, FG, GREEN, RED, ACC = "#0b1220", "#e8eefc", "#22c55e", "#ef4444", "#38bdf8"


def _style():
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                         "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
                         "axes.edgecolor": "#24324d", "font.size": 12})


def _footer(fig):
    fig.text(0.5, 0.012, f"{config.CHANNEL_NAME} • {config.PNL_NOTE} • Past results ≠ future returns • Not financial advice",
             ha="center", fontsize=9, color="#7f8db0")


def summary_card(st, ctx, period, path):
    """Big shareable scoreboard. st = stats for the period, ctx = 30-day stats (used for daily only)."""
    title, label = PERIODS[period][2], PERIODS[period][4]
    _style()
    fig = plt.figure(figsize=(8, 8))
    fig.text(0.5, 0.92, config.CHANNEL_NAME.upper(), ha="center", fontsize=20, weight="bold", color=ACC)
    fig.text(0.5, 0.87, title, ha="center", fontsize=13, color="#9fb0d6")
    col = GREEN if st["total_pct"] >= 0 else RED
    fig.text(0.5, 0.67, f"{st['total_pct']:+.2f}%", ha="center", fontsize=64, weight="bold", color=col)
    fig.text(0.5, 0.60, f"{st['trades']} trades  •  {st['wins']}W / {st['losses']}L  •  "
                        f"{st['win_rate']}% win rate", ha="center", fontsize=14)
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


def build_all(st, ctx, period, outdir):
    """Returns image paths. daily: card + 30-day charts; others: card + charts for the period itself."""
    paths = [f"{outdir}/summary.png"]
    summary_card(st, ctx, period, paths[0])
    series = ctx if period == "daily" else st
    cpd = "monthly" if period == "daily" else period
    if len(series["days"]) >= 2:
        equity_curve(series, cpd, f"{outdir}/equity.png"); paths.append(f"{outdir}/equity.png")
        bars(series, cpd, f"{outdir}/bars.png"); paths.append(f"{outdir}/bars.png")
    return paths
