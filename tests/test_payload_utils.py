from __future__ import annotations

from utils.payload_utils import summarize_large_fields


def test_summarize_large_fields_replaces_base64_data_without_mutating_payload() -> None:
    payload = {
        "input": {
            "image": {
                "content_type": "image/png",
                "filename": "street.png",
                "data": "a" * 80,
            },
            "threshold": 0.5,
        },
        "visualization": {"show_conf": True},
    }

    summary = summarize_large_fields(payload, max_string_length=20)

    assert summary["input"]["image"]["data"] == "<base64 length=80>"
    assert summary["input"]["threshold"] == 0.5
    assert payload["input"]["image"]["data"] == "a" * 80

def test_summarize_large_fields_only_replaces_large_data_fields() -> None:
    payload = {
        "request_id": "req-perception-preview",
        "input": {
            "image": {"data": "x" * 40},
        },
    }

    summary = summarize_large_fields(payload, max_string_length=10)

    assert summary["request_id"] == "req-perception-preview"
    assert summary["input"]["image"]["data"] == "<base64 length=40>"

