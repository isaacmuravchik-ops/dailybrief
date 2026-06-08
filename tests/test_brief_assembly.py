"""Tests for morning brief orchestration.

All external calls (sources, Claude, Telegram) are monkeypatched so no
network or real credentials are required.
"""

from unittest.mock import MagicMock, patch, call


@patch("src.brief.mark_reminder_sent")
@patch("src.brief.send")
@patch("src.brief.write_brief", return_value="Good morning!")
@patch("src.brief.get_due_reminders")
@patch("src.brief.get_fun_facts", return_value="1. Fact one\n2. Fact two\n3. Fact three")
@patch("src.brief.get_email", return_value="No email")
@patch("src.brief.get_calendar", return_value="No events")
@patch("src.brief.get_news", return_value="No news")
@patch("src.brief.get_weather", return_value="Sunny 72°F")
def test_main_calls_compose_and_send(
    mock_weather, mock_news, mock_calendar, mock_email,
    mock_facts, mock_reminders, mock_write_brief, mock_send, mock_mark_sent,
):
    one_off = {"id": 1, "text": "Buy milk", "due_date": "2026-06-08", "recurring": None}
    recurring = {"id": 2, "text": "Exercise", "due_date": "2026-06-01", "recurring": "daily"}
    mock_reminders.return_value = [one_off, recurring]

    from src.brief import main
    main()

    # compose was called with all six inputs including facts
    mock_write_brief.assert_called_once_with(
        "Sunny 72°F",
        "No news",
        "No events",
        "No email",
        [one_off, recurring],
        "1. Fact one\n2. Fact two\n3. Fact three",
    )

    # send was called exactly once
    mock_send.assert_called_once_with("Good morning!")

    # only the non-recurring reminder gets marked sent
    mock_mark_sent.assert_called_once_with(1)


@patch("src.brief.mark_reminder_sent")
@patch("src.brief.send")
@patch("src.brief.write_brief", return_value="Brief text")
@patch("src.brief.get_due_reminders", return_value=[])
@patch("src.brief.get_fun_facts", return_value="1. A fact\n2. Another\n3. Third")
@patch("src.brief.get_email", return_value="email")
@patch("src.brief.get_calendar", return_value="calendar")
@patch("src.brief.get_news", return_value="news")
@patch("src.brief.get_weather", return_value="weather")
def test_no_reminders_no_mark_sent(
    mock_weather, mock_news, mock_calendar, mock_email,
    mock_facts, mock_reminders, mock_write_brief, mock_send, mock_mark_sent,
):
    from src.brief import main
    main()

    mock_send.assert_called_once()
    mock_mark_sent.assert_not_called()
