"""Supabase-backed reminder storage and recurrence logic.

Reminders have four recurrence modes:
  null    — one-off; fires on due_date, then marked sent.
  daily   — fires every day on or after due_date.
  weekly  — fires on the same weekday as due_date, on or after due_date.
  monthly — fires on the same day-of-month as due_date, on or after due_date.
            NOTE: monthly reminders whose due_date.day is 29-31 will simply
            not fire in months that are too short — no clamping is attempted.

Supabase calls use the service-role key (server-side only) and raise on HTTP
errors so failures are visible rather than silently skipped.
"""

from __future__ import annotations

import datetime
from typing import Optional

import requests

from src.config import config

_BASE = f"{config.supabase_url}/rest/v1"
_HEADERS = {
    "apikey": config.supabase_service_key,
    "Authorization": f"Bearer {config.supabase_service_key}",
    "Content-Type": "application/json",
}


# ── Pure recurrence logic ────────────────────────────────────────────────────

def recurs_today(reminder: dict, today_iso: str) -> bool:
    """Return True if *reminder* is due on *today_iso* (YYYY-MM-DD).

    Handles all four recurrence modes.  Does NOT consult the database.
    """
    today = datetime.date.fromisoformat(today_iso)
    due = datetime.date.fromisoformat(reminder["due_date"])

    if today < due:
        return False

    recurring = reminder.get("recurring")

    if recurring is None:
        return today == due and not reminder.get("sent", False)
    if recurring == "daily":
        return True
    if recurring == "weekly":
        return today.weekday() == due.weekday()
    if recurring == "monthly":
        return today.day == due.day
    return False


# ── Supabase CRUD ────────────────────────────────────────────────────────────

def add_reminder(
    text: str,
    due_date: str,
    recurring: Optional[str] = None,
) -> dict:
    """Insert a new reminder row and return the created record."""
    payload = {"text": text, "due_date": due_date, "recurring": recurring}
    resp = requests.post(
        f"{_BASE}/reminders",
        json=payload,
        headers={**_HEADERS, "Prefer": "return=representation"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()[0]


def get_due_reminders(today_iso: str) -> list[dict]:
    """Return all reminders due today.

    Fetches non-recurring unsent rows due today plus all recurring rows,
    then filters recurring ones through recurs_today in Python.
    """
    # Non-recurring: due today and not yet sent
    params_one_off = {
        "recurring": "is.null",
        "due_date": f"eq.{today_iso}",
        "sent": "eq.false",
    }
    r1 = requests.get(
        f"{_BASE}/reminders",
        params=params_one_off,
        headers=_HEADERS,
        timeout=15,
    )
    r1.raise_for_status()
    one_off = r1.json()

    # Recurring: all rows where recurring is not null
    r2 = requests.get(
        f"{_BASE}/reminders",
        params={"recurring": "not.is.null"},
        headers=_HEADERS,
        timeout=15,
    )
    r2.raise_for_status()
    recurring_rows = [r for r in r2.json() if recurs_today(r, today_iso)]

    return one_off + recurring_rows


def mark_reminder_sent(reminder_id: int) -> None:
    """Set sent=true on a one-off reminder after it fires."""
    resp = requests.patch(
        f"{_BASE}/reminders",
        params={"id": f"eq.{reminder_id}"},
        json={"sent": True},
        headers=_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
