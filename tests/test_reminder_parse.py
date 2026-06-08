"""Tests for Claude reminder parsing with mocked Anthropic client."""

import json
import pytest
from unittest.mock import MagicMock, patch

from src.compose import parse_reminder


def _mock_response(text: str):
    """Build a fake anthropic Messages response object."""
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


@patch("src.compose._client")
def test_parse_one_off(mock_client):
    payload = {"text": "Call dentist", "due_date": "2026-06-10", "recurring": None}
    mock_client.messages.create.return_value = _mock_response(json.dumps(payload))

    result = parse_reminder("call the dentist on Wednesday", "2026-06-08")
    assert result["text"] == "Call dentist"
    assert result["due_date"] == "2026-06-10"
    assert result["recurring"] is None


@patch("src.compose._client")
def test_parse_recurring_weekly(mock_client):
    payload = {"text": "Call mom", "due_date": "2026-06-08", "recurring": "weekly"}
    mock_client.messages.create.return_value = _mock_response(json.dumps(payload))

    result = parse_reminder("remind me to call mom every Monday", "2026-06-08")
    assert result["recurring"] == "weekly"


@patch("src.compose._client")
def test_parse_strips_json_fence(mock_client):
    payload = {"text": "Take vitamins", "due_date": "2026-06-08", "recurring": "daily"}
    fenced = f"```json\n{json.dumps(payload)}\n```"
    mock_client.messages.create.return_value = _mock_response(fenced)

    result = parse_reminder("take vitamins every day", "2026-06-08")
    assert result["text"] == "Take vitamins"
    assert result["recurring"] == "daily"


@patch("src.compose._client")
def test_parse_malformed_raises(mock_client):
    mock_client.messages.create.return_value = _mock_response("not valid json at all")

    with pytest.raises(ValueError, match="non-JSON"):
        parse_reminder("do something", "2026-06-08")
