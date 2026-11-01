"""'Bounce vs dump' market outlook chart in the style of a trading-terminal screenshot."""
from datetime import datetime, timezone
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from . import config
from .scenario import key_level_text, human
from .signal_chart import fmt, BG, GRID, UP, DN, GREEN, RED, GOLD, FG

MUTED = "#8b95a9"


def scenario_chart(base, candles, lv, interval, source, path):
    plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG, "text.color": FG,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    fig = plt.figure(figsize=(11.68, 7.84), dpi=100)
    ax = fig.add_axes([0.02, 0.30, 0.865, 0.50], facecolor=BG)
    vx = fig.add_axes([0.02, 0.165, 0.865, 0.095], facecolor=BG, sharex=ax)
    n = len(candles); pad = max(30, int(n * 0.45))
    for i, (t, o, h, l, c, v) in enumerate(candles):
        col = UP if c >= o else DN
        ax.plot([i, i], [l, h], color=col, lw=1.1, zorder=3)
        ax.add_patch(plt.Rectangle((i - 0.33, min(o, c)), 0.66, max(abs(c - o), 1e-12), color=col, zorder=4))
        vx.bar(i, v * c, width=0.7, color=col, alpha=0.8)
    last = lv["last"]
    lo = min(lv["major"], min(c[3] for c in candles)); hi = max(lv["resistance"], max(c[2] for c in candles))
    span = hi - lo
    ax.set_ylim(lo - span * 0.07, hi + span * 0.07); ax.set_xlim(-1, n + pad)
    xr = n + pad

    # resistance / major support lines + support zone band
    ax.axhline(lv["resistance"], color=RED, ls="--", lw=1.3, zorder=2)
    ax.axhline(lv["major"], color=MUTED, ls="--", lw=1.3, zorder=2)
    ax.axhspan(lv["zone"][0], lv["zone"][1], xmin=0.30, xmax=0.98, color="#2f8f4e", alpha=0.20, zorder=1)
    ax.add_patch(plt.Rectangle((n * 0.30, lv["zone"][0]), xr * 0.68 - n * 0.30 + n * 0.3, lv["zone"][1] - lv["zone"][0], fill=False, ec="#2f8f4e", lw=1, zorder=2)) if False else None
    ax.axhline(last, color=RED if lv["chg24"] < 0 else GREEN, ls=":", lw=1, zorder=2)
    ax.text(n * 0.31, (lv["zone"][0] + lv["zone"][1]) / 2, "SUPPORT ZONE", color=GOLD, fontsize=11, weight="bold", va="center", zorder=6)
    ax.text(1, lv["resistance"], " RESISTANCE ", color=RED, fontsize=10.5, weight="bold", va="center", zorder=6,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec=RED, lw=1.2))
    ax.text(1, lv["major"], " SUPPORT ", color="#cdd5e4", fontsize=10.5, weight="bold", va="center", zorder=6,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec=MUTED, lw=1.2))

    # right-axis price tags
    def tag(p, color, txt=None, fg=FG):
        ax.text(xr + 0.3, p, txt or fmt(p), color=fg, fontsize=10, weight="bold", va="center", ha="left", clip_on=False,
                zorder=7, bbox=dict(boxstyle="square,pad=0.3", fc=color, ec=color))
    tag(lv["resistance"], RED); tag(lv["major"], "#6b7385")
    tag(lv["zone_mid"], GOLD, fg=BG)
    tag(last, RED if lv["chg24"] < 0 else "#1f8f4e", f"{fmt(last)}\n{lv['chg24']:+.2f}%")

    # scenario arrows from the last candle
    x0, y0 = n - 1, last
    ax.add_patch(FancyArrowPatch((x0 + 1, y0), (x0 + pad * 0.42, lv["resistance"] - span * 0.02), connectionstyle="arc3,rad=-0.35",
                                 arrowstyle="-|>", mutation_scale=22, lw=2.4, color=GREEN, zorder=8))
    ax.add_patch(FancyArrowPatch((x0 + 1, y0), (x0 + pad * 0.42, lv["major"] + (lv["zone"][0] - lv["major"]) * 0.35), connectionstyle="arc3,rad=0.35",
                                 arrowstyle="-|>", mutation_scale=22, lw=2.4, color=RED, zorder=8))
    tx = x0 + pad * 0.40
    tr = ax.get_xaxis_transform()          # x in data units, y as fraction of the axes: labels never depend on price levels
    mask = dict(boxstyle="round,pad=0.35", fc=BG, ec="none", alpha=0.88)
    ax.text(tx, 0.80, "BOUNCE SCENARIO", color=GREEN, fontsize=13, weight="bold", va="bottom", transform=tr, zorder=9, bbox=mask)
    ax.text(tx, 0.795, "Hold support and rally\ntoward resistance", color=FG, fontsize=10.5, va="top", transform=tr, zorder=9, bbox=mask)
    ax.text(tx, 0.20, "DUMP SCENARIO", color=RED, fontsize=13, weight="bold", va="bottom", transform=tr, zorder=9, bbox=mask)
    ax.text(tx, 0.195, "Break below support\nand retest lower level", color=FG, fontsize=10.5, va="top", transform=tr, zorder=9, bbox=mask)

    step = max(1, n // 8)
    vx.set_xticks(range(0, n, step))
    vx.set_xticklabels([datetime.fromtimestamp(candles[i][0] / 1000, timezone.utc).strftime("%H:%M\n%d %b") for i in range(0, n, step)], fontsize=9)
    plt.setp(ax.get_xticklabels(), visible=False)
    for a in (ax, vx):
        a.yaxis.tick_right(); a.grid(color=GRID, lw=0.8); [s.set_visible(False) for s in a.spines.values()]
        a.tick_params(length=0)
    ax.tick_params(axis="y", labelsize=9); vx.tick_params(axis="y", labelsize=0); vx.yaxis.offsetText.set_visible(False)
    fig.text(0.025, 0.268, f"VOLUME (USDT)  ", color=MUTED, fontsize=9.5); fig.text(0.125, 0.268, human(lv["vol24"]), color=GREEN, fontsize=9.5, weight="bold")

    # header
    from matplotlib.patches import Circle
    from matplotlib.patches import Ellipse
    fig.patches.append(Ellipse((0.047, 0.915), 0.056, 0.056 * 11.68 / 7.84, transform=fig.transFigure, fc="#f7931a", ec="none", figure=fig))
    fig.text(0.047, 0.915, "B" if base != "BTC" else "₿", color="white", fontsize=22, weight="bold", ha="center", va="center")
    fig.text(0.092, 0.935, f"{base}USDT", fontsize=26, weight="bold")
    fig.text(0.092, 0.885, f"{base} / TetherUS · {source.upper()} · {interval} chart", fontsize=11, color=MUTED)
    stats = [("LAST PRICE", fmt(last), FG), ("24H CHANGE", f"{lv['chg24']:+.2f}%", RED if lv["chg24"] < 0 else GREEN),
             ("24H HIGH", fmt(lv["high24"]), FG), ("24H LOW", fmt(lv["low24"]), FG), ("24H VOLUME", f"{human(lv['vol24'])} USDT", FG)]
    for i, (k, v, col) in enumerate(stats):
        x = 0.46 + i * 0.1
        fig.text(x, 0.94, k, fontsize=9.5, color=MUTED); fig.text(x, 0.905, v, fontsize=14, weight="bold", color=col)
    l1, l2 = key_level_text(base, lv, fmt)
    fig.text(0.02, 0.062, "Key Level in Focus:", fontsize=11.5, weight="bold", color=GOLD)
    fig.text(0.155, 0.062, l1, fontsize=11.5); fig.text(0.02, 0.028, l2, fontsize=10.5, color=MUTED)
    fig.text(0.98, 0.028, f"{config.CHANNEL_NAME} · Not financial advice · Trade with caution", fontsize=9.5, color=MUTED, ha="right")
    fig.savefig(path, dpi=100); plt.close(fig)
    return path
