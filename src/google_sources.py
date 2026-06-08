"""Google Calendar and Gmail read-only clients.

Builds OAuth credentials from a long-lived refresh token (no interactive flow
at runtime). All public functions degrade gracefully on error.

Scopes used:
  https://www.googleapis.com/auth/calendar.readonly
  https://www.googleapis.com/auth/gmail.readonly
"""

from __future__ import annotations

import datetime
import re

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config import config

_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]
_TOKEN_URI = "https://oauth2.googleapis.com/token"


def _google_creds() -> Credentials:
    """Build OAuth2 credentials from the configured refresh token."""
    return Credentials(
        token=None,
        refresh_token=config.google_refresh_token,
        token_uri=_TOKEN_URI,
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        scopes=_SCOPES,
    )


def _trim_sender(raw: str) -> str:
    """Extract display name from a From header, falling back to the email."""
    match = re.match(r'^"?([^"<]+)"?\s*<', raw)
    if match:
        return match.group(1).strip()
    email_match = re.match(r"[^@<\s]+@[^\s>]+", raw)
    if email_match:
        return email_match.group(0)
    return raw.strip()


def _format_event_time(event: dict, tz: datetime.timezone) -> str:
    """Return a display string for an event's start time."""
    start = event.get("start", {})
    if "dateTime" in start:
        dt = datetime.datetime.fromisoformat(start["dateTime"])
        return dt.strftime("%-I:%M %p")
    return "all day"


def get_calendar() -> str:
    """Return today's primary-calendar events as a formatted string.

    Never raises — returns an error string on failure.
    """
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(config.timezone)
        creds = _google_creds()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.datetime.now(tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + datetime.timedelta(days=1)

        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = result.get("items", [])

        if not events:
            return "No events scheduled."

        lines = []
        for event in events:
            time_str = _format_event_time(event, tz)
            summary = event.get("summary", "(no title)")
            lines.append(f"- {time_str}: {summary}")
        return "\n".join(lines)
    except Exception as e:
        return f"(calendar unavailable: {e})"


def get_email(limit: int = 8) -> str:
    """Return unread important/inbox emails from the last day.

    Never raises — returns an error string on failure.
    """
    try:
        creds = _google_creds()
        service = build("gmail", "v1", credentials=creds)

        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                q="is:unread (is:important OR in:inbox) newer_than:1d",
                maxResults=limit,
            )
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return "No important unread email."

        lines = []
        for msg in messages:
            detail = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata",
                     metadataHeaders=["From", "Subject"])
                .execute()
            )
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            sender = _trim_sender(headers.get("From", "Unknown"))
            subject = headers.get("Subject", "(no subject)")
            lines.append(f"- {sender}: {subject}")
        return "\n".join(lines)
    except Exception as e:
        return f"(email unavailable: {e})"
