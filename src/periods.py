"""Report periods. Windows are rolling (last N days) so a run on any day gives a sensible report."""
PERIODS = {
    #            days, bucket, title,           bar chart title,        label
    "daily":   (1,   "day",   "DAILY RESULTS",   "Daily P&L (%)",       "Today"),
    "weekly":  (7,   "day",   "WEEKLY RESULTS",  "P&L per day (%)",     "This week"),
    "monthly": (30,  "day",   "MONTHLY RESULTS", "P&L per day (%)",     "This month"),
    "yearly":  (365, "month", "YEARLY RESULTS",  "P&L per month (%)",   "This year"),
}


def window(period, ref_date, tz):
    """Calendar window that CONTAINS ref_date, in timezone tz.
    daily = that day; weekly = Mon-Sun week; monthly = calendar month; yearly = calendar year.
    Returns (start, end_exclusive, label) as tz-aware datetimes + a display label."""
    from datetime import datetime, timedelta, time
    d0 = lambda d: datetime.combine(d, time.min, tzinfo=tz)
    if period == "daily":
        s, e, label = ref_date, ref_date + timedelta(days=1), ref_date.strftime("%d %b %Y").upper()
    elif period == "weekly":
        s = ref_date - timedelta(days=ref_date.weekday()); e = s + timedelta(days=7)
        last = e - timedelta(days=1)
        label = f"{s.strftime('%d %b')} – {last.strftime('%d %b %Y')}".upper()
    elif period == "monthly":
        s = ref_date.replace(day=1)
        e = (s + timedelta(days=32)).replace(day=1)
        label = s.strftime("%B %Y").upper()
    else:
        s, e, label = ref_date.replace(month=1, day=1), ref_date.replace(year=ref_date.year + 1, month=1, day=1), str(ref_date.year)
    return d0(s), d0(e), label
