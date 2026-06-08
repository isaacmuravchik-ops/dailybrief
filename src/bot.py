"""Flask webhook entrypoint for the Telegram reminder bot.

Handles incoming Telegram updates:
  /start  — greet and show the chat ID (helps the user capture TELEGRAM_CHAT_ID)
  /list   — list today's due reminders
  <text>  — parse as a natural-language reminder via Claude and store in Supabase

Single-user security: ignores messages from any chat ID other than the
configured TELEGRAM_CHAT_ID (when set).

Deploy on Railway/Render/Fly. Register the webhook with:
  curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<host>/webhook"
"""

import datetime

from flask import Flask, request, jsonify

from src.config import config
from src.compose import parse_reminder
from src.reminders import add_reminder, get_due_reminders
from src.telegram import send

app = Flask(__name__)


@app.get("/")
def health():
    return "ok", 200


@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message")
    if not message:
        return jsonify(ok=True)

    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()

    # Single-user lockdown
    if config.telegram_chat_id and chat_id != str(config.telegram_chat_id):
        return jsonify(ok=True)

    if text == "/start":
        send(
            f"👋 Morning brief bot is running!\nYour chat ID is `{chat_id}` — "
            "set it as TELEGRAM_CHAT_ID in your environment.",
            chat_id=chat_id,
        )
        return jsonify(ok=True)

    if text == "/list":
        today = datetime.date.today().isoformat()
        try:
            due = get_due_reminders(today)
            if due:
                lines = "\n".join(f"• {r['text']} ({r['due_date']})" for r in due)
                reply = f"*Today's reminders:*\n{lines}"
            else:
                reply = "No reminders due today."
        except Exception as e:
            reply = f"(could not fetch reminders: {e})"
        send(reply, chat_id=chat_id)
        return jsonify(ok=True)

    # Natural-language reminder ingestion
    today = datetime.date.today().isoformat()
    try:
        parsed = parse_reminder(text, today)
        add_reminder(
            text=parsed["text"],
            due_date=parsed["due_date"],
            recurring=parsed.get("recurring"),
        )
        recur_note = f" ({parsed['recurring']})" if parsed.get("recurring") else ""
        send(
            f"✅ Reminder saved: *{parsed['text']}* on {parsed['due_date']}{recur_note}",
            chat_id=chat_id,
        )
    except Exception as e:
        send(
            "Sorry, I couldn't understand that as a reminder. "
            "Try something like: *'remind me to call mom every Sunday'*",
            chat_id=chat_id,
        )

    return jsonify(ok=True)
