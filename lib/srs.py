"""Spaced repetition helper utilities."""
from __future__ import annotations

import datetime as dt
from typing import Optional

INTERVAL_LABELS = [
    (0, "New"),
    (1, "Learning"),
    (7, "Short-Term"),
    (30, "Medium-Term"),
]


def humanize_interval(days: int) -> str:
    """Convert an interval in days into a human readable label."""
    if days <= 0:
        return "due now"
    if days == 1:
        return "1 day"
    if days < 7:
        return f"{days} days"
    weeks = days / 7
    if weeks < 4:
        return f"{weeks:.1f} weeks"
    months = days / 30
    return f"{months:.1f} months"


def due_status(due_at: Optional[str]) -> str:
    """Return a friendly label for a due date."""
    if not due_at:
        return "Unknown"
    due_date = dt.datetime.fromisoformat(str(due_at)).date()
    today = dt.date.today()
    delta = (due_date - today).days
    if delta < 0:
        return "Overdue"
    if delta == 0:
        return "Due today"
    if delta == 1:
        return "Due tomorrow"
    return f"Due in {delta} days"


def streak_from_reviews(review_dates: list[dt.date]) -> int:
    """Calculate consecutive review streak from a list of review dates."""
    if not review_dates:
        return 0
    unique_days = sorted(set(review_dates), reverse=True)
    streak = 0
    expected = dt.date.today()
    for day in unique_days:
        if day == expected:
            streak += 1
            expected -= dt.timedelta(days=1)
        elif day == expected - dt.timedelta(days=streak):
            streak += 1
            expected = day - dt.timedelta(days=1)
        else:
            break
    return streak
