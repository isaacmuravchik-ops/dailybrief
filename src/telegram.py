"""Telegram message delivery helper.

Sends a message to the configured chat using the Bot API.
Raises on HTTP error — delivery failures should be loud.
"""

import requests
from src.config import config


def send(text: str, chat_id: str | None = None) -> None:
    """Send *text* to the owner's Telegram chat.

    Uses Markdown parse mode and suppresses link previews.
    Raises requests.HTTPError on delivery failure.
    """
    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id or config.telegram_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
