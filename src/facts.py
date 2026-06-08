"""Daily fun facts generator.

Uses Claude to produce 3 fresh, interesting fun facts each morning.
Never raises — returns a fallback string on any failure.
"""

import anthropic
from src.config import config

_client = anthropic.Anthropic(api_key=config.anthropic_api_key)


def get_fun_facts() -> str:
    """Return 3 interesting fun facts as a formatted string.

    Facts are generated fresh each call so they vary daily.
    Never raises — returns an error string on failure.
    """
    try:
        response = _client.messages.create(
            model="claude-opus-4-8",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "Give me exactly 3 genuinely interesting, surprising fun facts. "
                    "Cover different topics each time (science, history, nature, food, "
                    "geography, language, etc). Be specific — avoid vague or well-known facts. "
                    "Format as a simple numbered list, one fact per line, no intro sentence."
                ),
            }],
        )
        return "".join(
            block.text for block in response.content if hasattr(block, "text")
        ).strip()
    except Exception as e:
        return f"(fun facts unavailable: {e})"
