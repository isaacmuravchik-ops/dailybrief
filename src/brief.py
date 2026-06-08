"""Morning brief batch entrypoint.

Orchestrates all data sources, calls Claude to compose the brief, delivers
it via Telegram, then marks non-recurring reminders as sent.

Each source is wrapped in its own try/except so a single failure degrades
that section only — the brief still sends.

Run directly:
    python src/brief.py
"""

import datetime
from zoneinfo import ZoneInfo

from src.config import config
from src.weather import get_weather
from src.news import get_news
from src.google_sources import get_calendar, get_email
from src.reminders import get_due_reminders, mark_reminder_sent
from src.compose import write_brief
from src.telegram import send


def main() -> None:
    today = datetime.date.today().isoformat()

    try:
        weather = get_weather()
    except Exception as e:
        weather = f"(weather unavailable: {e})"

    try:
        news = get_news()
    except Exception as e:
        news = f"(news unavailable: {e})"

    try:
        calendar = get_calendar()
    except Exception as e:
        calendar = f"(calendar unavailable: {e})"

    try:
        email = get_email()
    except Exception as e:
        email = f"(email unavailable: {e})"

    try:
        reminders = get_due_reminders(today)
    except Exception as e:
        reminders = []
        print(f"[brief] reminders fetch failed: {e}")

    brief_text = write_brief(weather, news, calendar, email, reminders)
    send(brief_text)

    # Mark non-recurring reminders sent
    for r in reminders:
        if r.get("recurring") is None:
            try:
                mark_reminder_sent(r["id"])
            except Exception as e:
                print(f"[brief] failed to mark reminder {r['id']} sent: {e}")

    print(f"[brief] delivered successfully ({today})")


if __name__ == "__main__":
    main()
