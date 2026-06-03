from __future__ import annotations

from typing import Any


def summarize_large_fields(payload: Any, max_string_length: int = 120) -> Any:
    """Create a JSON-preview-safe copy of a render request payload.

    Args:
        payload: Arbitrary JSON-compatible value from a render request payload.
        max_string_length: `data` strings longer than this value are replaced by
            a length marker so previews remain readable.

    Returns:
        A deep summary copy of the payload where oversized `data` strings are
        replaced with a `<base64 length=N>` marker and other strings are kept.
    """
    return _summarize_large_fields(payload, max_string_length=max_string_length, key=None)


def _summarize_large_fields(payload: Any, max_string_length: int, key: str | None) -> Any:
    """Recursively summarize large payload fields while preserving non-data strings.

    Args:
        payload: JSON-compatible value to summarize.
        max_string_length: Maximum length before a `data` string is summarized.
        key: Dictionary key that led to the current value.

    Returns:
        Summarized JSON-compatible value.
    """
    if isinstance(payload, dict):
        return {
            child_key: _summarize_large_fields(value, max_string_length, child_key)
            for child_key, value in payload.items()
        }

    if isinstance(payload, list):
        return [_summarize_large_fields(value, max_string_length, key) for value in payload]

    if key == "data" and isinstance(payload, str) and len(payload) > max_string_length:
        return f"<base64 length={len(payload)}>"

    return payload
