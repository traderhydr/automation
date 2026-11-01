"""Eye-catching, dark-themed charts built from the real trade data."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import config

BG, FG, GREEN, RED, ACC = "#0b1220", "#e8eefc", "#22c55e", "#ef4444", "#38bdf8"


def _style():
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                         "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
                         "axes.edgecolor": "#24324d", "font.size": 12})


def _footer(fig):
    fig.text(0.5, 0.012, f"{config.CHANNEL_NAME} • Past results ≠ future returns • Not financial advice",
             ha="center", fontsize=9, color="#7f8db0")


def summary_card(today, month, path):
    """Big shareable 'scoreboard' image for today's results."""
    _style()
    fig = plt.figure(figsize=(8, 8))
    fig.text(0.5, 0.92, config.CHANNEL_NAME.upper(), ha="center", fontsize=20, weight="bold", color=ACC)
    fig.text(0.5, 0.87, "DAILY RESULTS", ha="center", fontsize=13, color="#9fb0d6")
    col = GREEN if today["total_pct"] >= 0 else RED
    fig.text(0.5, 0.67, f"{today['total_pct']:+.2f}%", ha="center", fontsize=64, weight="bold", color=col)
    fig.text(0.5, 0.60, f"{today['trades']} trades  •  {today['wins']}W / {today['losses']}L  •  "
                        f"{today['win_rate']}% win rate", ha="center", fontsize=14)
    pf = month["profit_factor"] if month["profit_factor"] is not None else "–"
    tiles = [("30-DAY P&L", f"{month['total_pct']:+.1f}%"), ("30-DAY WIN RATE", f"{month['win_rate']}%"),
             ("PROFIT FACTOR", f"{pf}"), ("MAX DRAWDOWN", f"-{month['max_drawdown']}%")]
    for i, (k, v) in enumerate(tiles):
        x = 0.14 + (i % 2) * 0.40
        y = 0.36 - (i // 2) * 0.18
        fig.text(x, y + 0.05, k, fontsize=11, color="#9fb0d6")
        fig.text(x, y, v, fontsize=26, weight="bold")
    _footer(fig)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def equity_curve(month, path):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    x = list(range(len(month["days"])))
    ax.plot(x, month["equity"], color=ACC, lw=3)
    ax.fill_between(x, month["equity"], 0, color=ACC, alpha=0.15)
    ax.axhline(0, color="#475569", lw=1)
    ax.set_xticks(x[::max(1, len(x) // 8)])
    ax.set_xticklabels([month["days"][i][5:] for i in x[::max(1, len(x) // 8)]])
    ax.set_ylabel("Cumulative return (%)")
    ax.set_title(f"Equity curve – last {len(x)} trading days:  {month['total_pct']:+.1f}%",
                 fontsize=16, weight="bold", loc="left")
    ax.grid(alpha=0.12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _footer(fig)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def daily_bars(month, path):
    _style()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    cols = [GREEN if v >= 0 else RED for v in month["daily"]]
    ax.bar([d[5:] for d in month["days"]], month["daily"], color=cols)
    ax.axhline(0, color="#475569", lw=1)
    ax.set_title("Daily P&L (%)", fontsize=16, weight="bold", loc="left")
    plt.setp(ax.get_xticklabels(), rotation=60, ha="right", fontsize=9)
    ax.grid(axis="y", alpha=0.12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _footer(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def build_all(today, month, outdir):
    paths = [f"{outdir}/summary.png"]
    summary_card(today, month, paths[0])
    if len(month["days"]) >= 2:
        equity_curve(month, f"{outdir}/equity.png"); paths.append(f"{outdir}/equity.png")
        daily_bars(month, f"{outdir}/daily.png"); paths.append(f"{outdir}/daily.png")
    return paths
