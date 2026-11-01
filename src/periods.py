"""Report periods. Windows are rolling (last N days) so a run on any day gives a sensible report."""
PERIODS = {
    #            days, bucket, title,           bar chart title,        label
    "daily":   (1,   "day",   "DAILY RESULTS",   "Daily P&L (%)",       "Today"),
    "weekly":  (7,   "day",   "WEEKLY RESULTS",  "P&L per day (%)",     "This week"),
    "monthly": (30,  "day",   "MONTHLY RESULTS", "P&L per day (%)",     "This month"),
    "yearly":  (365, "month", "YEARLY RESULTS",  "P&L per month (%)",   "This year"),
}
