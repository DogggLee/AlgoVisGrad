from __future__ import annotations

from components.perception_demo.vis_window import build_perception_payload


def test_build_perception_payload_uses_thresholds_and_visualization_flags() -> None:
    image_payload = {
        "content_type": "image/jpeg",
        "filename": "street.jpg",
        "data": "base64-image",
    }

    payload = build_perception_payload(
        image_payload=image_payload,
        iou_threshold=0.5,
        conf_threshold=0.35,
        show_class_id=True,
        show_conf=False,
        request_id="req-perception",
    )

    assert payload == {
        "input": {
            "image": image_payload,
            "iou_threshold": 0.5,
            "conf_threshold": 0.35,
        },
        "visualization": {
            "show_class_id": True,
            "show_conf": False,
        },
        "request_id": "req-perception",
    }
