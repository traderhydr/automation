from collections import defaultdict
from datetime import datetime


def _teaser(trades):
    ts = [t for t in trades if t.get("teaser")]
    return {"closed": len(ts), "wins": sum(1 for t in ts if t["pnl_pct"] > 0), "losses": sum(1 for t in ts if t["pnl_pct"] < 0),
            "total": round(sum(t["pnl_pct"] for t in ts), 2), "open": 0,
            "items": [[t["symbol"].replace("USDT", ""), round(t["pnl_pct"], 2)] for t in ts]}


def compute(trades, bucket="day"):
    """trades: list of trade dicts (any period). Returns stats dict."""
    n = len(trades)
    pnls = [t["pnl_pct"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_win, gross_loss = sum(wins), -sum(losses)
    daily = defaultdict(float)
    for t in trades:
        d = datetime.fromisoformat(t["date"]).date().isoformat()
        daily[d[:7] if bucket == "month" else d] += t["pnl_pct"]
    days = sorted(daily)
    equity, run, peak, max_dd = [], 0.0, 0.0, 0.0
    for d in days:
        run += daily[d]
        equity.append(run)
        peak = max(peak, run)
        max_dd = max(max_dd, peak - run)
    by_symbol = defaultdict(float)
    for t in trades:
        by_symbol[t["symbol"]] += t["pnl_pct"]
    return {
        "trades": n, "wins": len(wins), "losses": len(losses),
        "win_rate": round(100 * len(wins) / n, 1) if n else 0.0,
        "total_pct": round(sum(pnls), 2),
        "avg_win": round(sum(wins) / len(wins), 2) if wins else 0.0,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0.0,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else None,
        "best": round(max(pnls), 2) if pnls else 0.0,
        "worst": round(min(pnls), 2) if pnls else 0.0,
        "max_drawdown": round(max_dd, 2),
        "items": sorted(([t["symbol"].replace("USDT", ""), round(t["pnl_pct"], 2), bool(t.get("teaser"))] for t in trades), key=lambda x: -x[1]),
        "teaser": _teaser(trades),
        "first": min((t["date"] for t in trades), default=None),
        "last": max((t["date"] for t in trades), default=None),
        "days": days, "daily": [round(daily[d], 2) for d in days],
        "equity": [round(e, 2) for e in equity],
        "by_symbol": {k: round(v, 2) for k, v in sorted(by_symbol.items(), key=lambda x: -x[1])},
    }
