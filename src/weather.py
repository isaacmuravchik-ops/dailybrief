"""Open-Meteo weather client.

Fetches current conditions and today's forecast for the configured coordinates.
No API key required. On any error returns a safe fallback string so the brief
never crashes due to a weather failure.
"""

import requests
from src.config import config


def wmo_to_text(code: int) -> str:
    """Map a WMO weather interpretation code to a human-readable string."""
    _MAP = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        56: "light freezing drizzle",
        57: "heavy freezing drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        66: "light freezing rain",
        67: "heavy freezing rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        77: "snow grains",
        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        85: "slight snow showers",
        86: "heavy snow showers",
        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail",
    }
    return _MAP.get(code, "unknown")


def get_weather() -> str:
    """Return a one-line weather summary for today.

    Calls the Open-Meteo forecast API with current + daily data.
    Never raises — returns an error string on any failure.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": config.latitude,
            "longitude": config.longitude,
            "current": "temperature_2m,weathercode",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
            "temperature_unit": "fahrenheit",
            "timezone": config.timezone,
            "forecast_days": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data["current"]
        daily = data["daily"]

        temp_now = round(current["temperature_2m"])
        condition = wmo_to_text(current["weathercode"])
        temp_max = round(daily["temperature_2m_max"][0])
        temp_min = round(daily["temperature_2m_min"][0])
        precip_pct = daily["precipitation_probability_max"][0]

        return (
            f"{condition.capitalize()}, {temp_now}°F "
            f"(high {temp_max}°, low {temp_min}°, {precip_pct}% chance of precip)"
        )
    except Exception as e:
        return f"(weather unavailable: {e})"
