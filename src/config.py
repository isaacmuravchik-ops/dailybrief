"""Central environment-variable loading and validation.

All other modules import their settings from here. At import time, config.py
reads os.environ, applies defaults, and raises RuntimeError if a required
variable is missing, so misconfigured deploys fail immediately on startup.

Setup: copy .env.example to .env, fill in real values, then either
`export $(cat .env | xargs)` or use a tool like python-dotenv.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    telegram_chat_id: str
    anthropic_api_key: str
    supabase_url: str
    supabase_service_key: str
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    news_api_key: str | None
    timezone: str
    latitude: float
    longitude: float
    news_country: str
    port: int


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable {name!r} is not set. "
            "Copy .env.example to .env, fill in your values, and export them."
        )
    return value


def _load() -> Config:
    return Config(
        telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_require("TELEGRAM_CHAT_ID"),
        anthropic_api_key=_require("ANTHROPIC_API_KEY"),
        supabase_url=_require("SUPABASE_URL"),
        supabase_service_key=_require("SUPABASE_SERVICE_KEY"),
        google_client_id=_require("GOOGLE_CLIENT_ID"),
        google_client_secret=_require("GOOGLE_CLIENT_SECRET"),
        google_refresh_token=_require("GOOGLE_REFRESH_TOKEN"),
        news_api_key=os.environ.get("NEWS_API_KEY"),
        timezone=os.environ.get("TIMEZONE", "America/New_York"),
        latitude=float(os.environ.get("LATITUDE", "40.6782")),
        longitude=float(os.environ.get("LONGITUDE", "-73.9442")),
        news_country=os.environ.get("NEWS_COUNTRY", "us"),
        port=int(os.environ.get("PORT", "8080")),
    )


config = _load()
