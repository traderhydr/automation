"""QNT-style signal chart: candles + entry marker + TP / SL lines + risk:reward badge."""
import math
from datetime import datetime, timezone
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from . import config
from .signals import risk_reward
from . import branding

BG, GRID, UP, DN = "#0b0e14", "#1b212c", "#26a65b", "#e0453f"
GREEN, RED, BLUE, GOLD, FG = "#4ade80", "#f87171", "#60a5fa", "#f5c22b", "#e8eefc"


def fmt(p):
    dec = max(2, 3 - math.floor(math.log10(abs(p)))) if p else 2
    return f"{p:,.{dec}f}"


def signal_chart(sig, candles, interval, source, path):
    rr = risk_reward(sig)
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                         "text.color": FG, "axes.labelcolor": FG, "xtick.color": "#9aa4b8", "ytick.color": "#9aa4b8"})
    fig = plt.figure(figsize=(11.68, 7.84), dpi=100)
    ax = fig.add_axes([0.04, 0.115, 0.86, 0.63])
    n = len(candles)
    pad = max(14, n // 4)                         # empty space on the right for the labels
    for i, (t, o, h, l, c, v) in enumerate(candles):
        col = UP if c >= o else DN
        ax.plot([i, i], [l, h], color=col, lw=1.2, zorder=3)
        ax.add_patch(plt.Rectangle((i - 0.33, min(o, c)), 0.66, max(abs(c - o), 1e-12), color=col, zorder=4))
    lv = [x for x in sig["entries"] + sig["tps"] + [sig["sl"]]] + [k[2] for k in candles] + [k[3] for k in candles]
    lo, hi = min(lv), max(lv); span = hi - lo
    ax.set_ylim(lo - span * 0.10, hi + span * 0.10); ax.set_xlim(-1, n + pad)

    levels = [(tp["price"], GREEN, f"TP{i}  {tp['rr']}R", "--") for i, tp in enumerate(rr["tps"], 1)]
    levels += [(e, GOLD if i == 1 else BLUE, f"ENTRY {i}" if len(sig["entries"]) > 1 else "ENTRY", "--" if i == 1 else ":")
               for i, e in enumerate(sig["entries"], 1)]
    levels.append((sig["sl"], RED, f"SL  -{rr['risk_pct']}%", "--"))
    ylo, yhi = ax.get_ylim(); gap = (yhi - ylo) * 0.052
    order = sorted(range(len(levels)), key=lambda k: levels[k][0])
    ypos = {k: levels[k][0] for k in order}
    for _ in range(40):                                   # push labels apart so none overlap
        moved = False
        for a_, b_ in zip(order, order[1:]):
            if ypos[b_] - ypos[a_] < gap - 1e-12:
                mid = (ypos[a_] + ypos[b_]) / 2
                ypos[a_], ypos[b_] = mid - gap / 2, mid + gap / 2; moved = True
        if not moved: break
    for k, (price, color, label, style) in enumerate(levels):
        ax.axhline(price, color=color, ls=style, lw=1.4, alpha=0.9, zorder=2)
        y = ypos[k]
        if abs(y - price) > gap * 0.15:                   # leader line from the real level to its shifted label
            ax.plot([n + pad - 14, n + pad - 11], [price, y], color=color, lw=1, zorder=5)
        ax.text(n + pad - 0.5, y, f" {label} ", color=color, fontsize=11, weight="bold", ha="right", va="center",
                zorder=6, bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec=color, lw=1.2))
        ax.text(n + pad + 0.3, y, fmt(price), color=BG, fontsize=9.5, weight="bold", ha="left", va="center",
                zorder=6, clip_on=False, bbox=dict(boxstyle="square,pad=0.25", fc=color, ec=color))

    # where the trade opened
    fill = sig.get("fill")
    ex, ey = n - 1, (fill["price"] if fill else sig["entries"][0])
    if fill:
        ft = datetime.fromisoformat(fill["date"]).timestamp() * 1000
        ex = min(range(n), key=lambda i: abs(candles[i][0] - ft))
    ax.annotate("OPENED HERE" if fill else "ENTRY", xy=(ex, ey), xytext=(ex - max(8, n * 0.14), ey + (hi - lo) * (-0.12 if sig["side"] == "LONG" else 0.12)),
                color=FG, fontsize=12, weight="bold", ha="center", zorder=7,
                arrowprops=dict(arrowstyle="-|>", color=FG, lw=2),
                bbox=dict(boxstyle="round,pad=0.4", fc=BG, ec=FG, lw=1.2))
    ax.scatter([ex], [ey], s=90, color=GOLD, zorder=8, edgecolor=BG, linewidth=1.5)

    step = max(1, n // 7)
    ax.set_xticks(range(0, n, step))
    ax.set_xticklabels([datetime.fromtimestamp(candles[i][0] / 1000, timezone.utc).strftime("%d %b\n%H:%M") for i in range(0, n, step)], fontsize=9)
    ax.yaxis.tick_right(); ax.tick_params(axis="y", labelsize=0, length=0)
    ax.grid(color=GRID, lw=0.8); [s.set_visible(False) for s in ax.spines.values()]

    side_col = GREEN if sig["side"] == "LONG" else RED
    fig.text(0.04, 0.93, f"{sig['base']}", fontsize=44, weight="bold", color=side_col)
    fig.text(0.04, 0.868, f"{sig['base']} / USDT PERP · {interval} · {source.upper()} data", fontsize=13, color="#9aa4b8")
    badge = f"{sig['side']}" + (f" · {sig['leverage']}X" if sig["leverage"] else "")
    fig.text(0.04, 0.815, badge, fontsize=14, weight="bold", color=BG, va="center",
             bbox=dict(boxstyle="round,pad=0.45", fc=side_col, ec="none"))
    # R:R panel
    fr = rr["final_rr"]
    fig.text(0.90, 0.935, f"RISK : REWARD   1 : {fr}", fontsize=17, weight="bold", ha="right", color=GOLD)
    fig.text(0.90, 0.895, f"to TP{len(rr['tps'])} from Entry 1  ·  risk {rr['risk_pct']}% price move", fontsize=11, ha="right", color="#9aa4b8")
    fig.text(0.90, 0.862, "  ".join(f"TP{t['n']} {t['rr']}R" for t in rr["tps"]), fontsize=10.5, ha="right", color=GREEN)
    if sig.get("strategy"):
        fig.text(0.04, 0.02, f"Strategy: {sig['strategy']}", fontsize=11, color="#9aa4b8")
    ft = fig.text(0.96, 0.02, f"{config.CHANNEL_NAME} · Not financial advice · Trade with caution", fontsize=10, color="#7f8db0", ha="right")
    branding.add_logo_before_text(fig, ft, size_px=30)
    fig.savefig(path, dpi=100); plt.close(fig)
    return path
