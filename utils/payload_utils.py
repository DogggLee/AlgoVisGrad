from __future__ import annotations

from typing import Any


def summarize_large_fields(payload: Any, max_string_length: int = 120) -> Any:
    """Create a JSON-preview-safe copy of a render request payload.

    Args:
        payload: Arbitrary JSON-compatible value from a render request payload.
        max_string_length: Strings longer than this value are replaced by a
            length marker so previews remain readable.

    Returns:
        A deep summary copy of the payload where oversized strings are replaced
        with a `<base64 length=N>` marker and the original payload is unchanged.
    """
    if isinstance(payload, dict):
        return {key: summarize_large_fields(value, max_string_length) for key, value in payload.items()}

    if isinstance(payload, list):
        return [summarize_large_fields(value, max_string_length) for value in payload]

    if isinstance(payload, str) and len(payload) > max_string_length:
        return f"<base64 length={len(payload)}>"

    return payload
