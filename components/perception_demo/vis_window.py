from __future__ import annotations

from typing import Any


def build_perception_payload(
    image_payload: dict[str, Any],
    iou_threshold: float,
    conf_threshold: float,
    show_class_id: bool,
    show_conf: bool,
    request_id: str,
) -> dict[str, Any]:
    """Build the standard render request payload for the perception demo.

    Args:
        image_payload: Packed image payload with content_type, filename, and base64 data.
        iou_threshold: IoU threshold parameter sent to the perception algorithm.
        conf_threshold: Confidence threshold parameter sent to the perception algorithm.
        show_class_id: Whether the returned visualization should draw class IDs.
        show_conf: Whether the returned visualization should draw confidence values.
        request_id: Client-generated request identifier for debugging/reproduction.

    Returns:
        Render request payload using the platform `input`/`visualization` protocol.
    """
    return {
        "input": {
            "image": image_payload,
            "iou_threshold": iou_threshold,
            "conf_threshold": conf_threshold,
        },
        "visualization": {
            "show_class_id": show_class_id,
            "show_conf": show_conf,
        },
        "request_id": request_id,
    }
