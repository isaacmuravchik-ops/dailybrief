"""GNews top-headlines client.

Returns a formatted bullet list of current headlines.
Degrades gracefully when NEWS_API_KEY is absent — returns a notice string
instead of raising.
"""

import requests
from src.config import config


def get_news(limit: int = 6) -> str:
    """Fetch top headlines from GNews and return a bulleted string.

    Returns a notice string (never raises) on any error or missing key.
    """
    if not config.news_api_key:
        return "(no news API key configured)"

    try:
        url = "https://gnews.io/api/v4/top-headlines"
        params = {
            "category": "general",
            "lang": "en",
            "country": config.news_country,
            "max": limit,
            "apikey": config.news_api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])

        if not articles:
            return "(no headlines available)"

        lines = [f"• {a['title']} ({a['source']['name']})" for a in articles]
        return "\n".join(lines)
    except Exception as e:
        return f"(news unavailable: {e})"
