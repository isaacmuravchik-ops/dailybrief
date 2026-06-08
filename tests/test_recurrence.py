"""Unit tests for reminder recurrence logic.

Fixed "today" = 2026-06-08, which is a Monday (weekday 0).
The due_date for weekly tests is also a Monday so weekday assertions are stable.
"""

from src.reminders import recurs_today

TODAY = "2026-06-08"  # Monday


def _r(due_date, recurring=None, sent=False):
    return {"due_date": due_date, "recurring": recurring, "sent": sent, "id": 1}


# ── One-off ──────────────────────────────────────────────────────────────────

def test_one_off_due_today_unsent():
    assert recurs_today(_r("2026-06-08"), TODAY) is True


def test_one_off_due_today_already_sent():
    assert recurs_today(_r("2026-06-08", sent=True), TODAY) is False


def test_one_off_future():
    assert recurs_today(_r("2026-06-09"), TODAY) is False


def test_one_off_past():
    assert recurs_today(_r("2026-06-07"), TODAY) is False


# ── Daily ────────────────────────────────────────────────────────────────────

def test_daily_active():
    assert recurs_today(_r("2026-06-01", "daily"), TODAY) is True


def test_daily_not_yet_started():
    assert recurs_today(_r("2026-06-09", "daily"), TODAY) is False


def test_daily_same_day():
    assert recurs_today(_r("2026-06-08", "daily"), TODAY) is True


# ── Weekly ───────────────────────────────────────────────────────────────────

def test_weekly_matching_weekday():
    # due_date is 2026-06-01 (Monday) — today is also Monday
    assert recurs_today(_r("2026-06-01", "weekly"), TODAY) is True


def test_weekly_non_matching_weekday():
    # due_date is 2026-06-02 (Tuesday) — today is Monday
    assert recurs_today(_r("2026-06-02", "weekly"), TODAY) is False


def test_weekly_not_yet_started():
    # due_date in the future
    assert recurs_today(_r("2026-06-15", "weekly"), TODAY) is False


# ── Monthly ──────────────────────────────────────────────────────────────────

def test_monthly_same_day_of_month():
    # due_date is the 8th; today is the 8th
    assert recurs_today(_r("2026-05-08", "monthly"), TODAY) is True


def test_monthly_different_day():
    # due_date is the 7th; today is the 8th
    assert recurs_today(_r("2026-05-07", "monthly"), TODAY) is False


def test_monthly_not_yet_started():
    assert recurs_today(_r("2026-07-08", "monthly"), TODAY) is False
