"""Backfill trade history from a Cornix 'signals' CSV export.

    python -m src.import_csv export.csv [--tz UTC] [--until 2026-11-02] [--out data/trades.json]

Imports only signals that actually ENTERED and have FINISHED (>=1 filled entry, status not Buy/Sell = still open).
Open trades and never-entered signals are skipped. Close time = signal time + Duration.
Use --until so the import stops where your live Telegram pipeline starts (the two sources use different ids,
so overlapping periods would be counted twice).
"""
import argparse, csv, json, os, re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _mins(s):
    units = {"day": 1440, "d": 1440, "hr": 60, "h": 60, "min": 1, "m": 1}
    return sum(int(n) * units[u] for n, u in re.findall(r"(\d+)\s*(day|d|hr|h|min|m)\b", s or ""))


def load(path, tz="UTC"):
    z = ZoneInfo(tz)
    out, skipped = [], {"open": 0, "never_entered": 0}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        status = r["Status"].split("(")[0].strip()
        if int(r["Number of Filled Entry Targets"] or 0) == 0:
            skipped["never_entered"] += 1; continue
        if status in ("Buy", "Sell"):
            skipped["open"] += 1; continue
        t0 = datetime.fromisoformat(r["Date"]).replace(tzinfo=z)
        close = t0 + timedelta(minutes=_mins(r["Duration"]))
        sym = r["Symbol"].replace("/", "").upper()
        out.append({"id": f"csv:{r['Date']}:{sym}:{r['Direction']}", "date": close.isoformat(), "symbol": sym,
                    "side": r["Direction"].upper(), "pnl_pct": float(r["Signal Gained Profit %"]), "status": status})
    return out, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--tz", default="UTC", help="time zone of the Date column in the export")
    ap.add_argument("--until", help="only keep trades closed before this date (YYYY-MM-DD, in --tz)")
    ap.add_argument("--out", default=os.getenv("HISTORY_PATH", "data/trades.json"))
    a = ap.parse_args()
    trades, skipped = load(a.csv, a.tz)
    if a.until:
        cut = datetime.fromisoformat(a.until).replace(tzinfo=ZoneInfo(a.tz))
        trades = [t for t in trades if datetime.fromisoformat(t["date"]) < cut]
    hist = json.load(open(a.out)) if os.path.exists(a.out) else []
    seen = {t.get("id") for t in hist}
    new = [t for t in trades if t["id"] not in seen]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(hist + new, open(a.out, "w"), indent=1)
    print(f"imported {len(new)} closed trades (skipped: {skipped}) -> {a.out}  [{len(hist) + len(new)} total]")


if __name__ == "__main__":
    main()
