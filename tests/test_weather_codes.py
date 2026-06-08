"""Unit tests for WMO weather-code mapping."""

from src.weather import wmo_to_text


def test_clear():
    assert wmo_to_text(0) == "clear sky"


def test_partly_cloudy():
    assert wmo_to_text(2) == "partly cloudy"


def test_heavy_rain():
    assert wmo_to_text(65) == "heavy rain"


def test_thunderstorm():
    assert wmo_to_text(95) == "thunderstorm"


def test_thunderstorm_heavy_hail():
    assert wmo_to_text(99) == "thunderstorm with heavy hail"


def test_unknown_code():
    assert wmo_to_text(999) == "unknown"


def test_snow():
    assert wmo_to_text(71) == "slight snow"


def test_fog():
    assert wmo_to_text(45) == "fog"
