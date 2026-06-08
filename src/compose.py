"""Claude brief composition and reminder parsing.

Uses claude-opus-4-8 for both tasks:
  write_brief   — assembles a Telegram-formatted morning brief from five sources.
  parse_reminder — parses a natural-language message into a structured reminder dict.
"""

from __future__ import annotations

import json

import anthropic

from src.config import config

_client = anthropic.Anthropic(api_key=config.anthropic_api_key)


def write_brief(
    weather: str,
    news: str,
    calendar: str,
    email: str,
    reminders: list[dict],
) -> str:
    """Compose a morning brief and return it as a Telegram-ready string."""
    reminder_text = "\n".join(f"• {r['text']} (due {r['due_date']})" for r in reminders)
    if not reminder_text:
        reminder_text = "None"

    prompt = f"""You are a concise personal assistant composing a morning brief for Telegram.

Use Telegram *bold* labels (e.g. *Weather:*) — no # headers, no markdown headings.
Keep each section tight. If a section shows "(unavailable)", mention it briefly and move on.
Reminders must stand out — make them prominent.
End with one short encouraging line.

Here is the data:

*Weather:* {weather}

*Calendar:*
{calendar}

*Reminders:*
{reminder_text}

*Email:*
{email}

*News:*
{news}

Write the brief now."""

    response = _client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if hasattr(block, "text"))


def parse_reminder(message: str, today: str) -> dict:
    """Parse a natural-language message into a reminder dict.

    Returns a dict with keys: text (str), due_date (YYYY-MM-DD str),
    recurring (null | 'daily' | 'weekly' | 'monthly').
    Raises ValueError if the response cannot be parsed as valid JSON.
    """
    prompt = f"""Today is {today}. The user sent this message to set a reminder:

\"{message}\"

Extract the reminder and respond with JSON ONLY (no explanation, no code fences):
{{
  "text": "<reminder description>",
  "due_date": "<YYYY-MM-DD, resolved from today>",
  "recurring": <null | "daily" | "weekly" | "monthly">
}}"""

    response = _client.messages.create(
        model="claude-opus-4-8",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(block.text for block in response.content if hasattr(block, "text")).strip()

    # Strip optional ```json ... ``` fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON: {raw!r}") from e
