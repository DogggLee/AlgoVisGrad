from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

from components.perception_demo.mock_server import RENDER_DEBUG_PATH, create_perception_demo_mock_app


def test_perception_demo_mock_server_health_endpoint_reports_ok() -> None:
    app = create_perception_demo_mock_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_perception_demo_mock_server_render_endpoint_returns_base64_png() -> None:
    app = create_perception_demo_mock_app()
    client = app.test_client()
    debug_backup = RENDER_DEBUG_PATH.read_bytes() if RENDER_DEBUG_PATH.exists() else None

    image = Image.new("RGB", (32, 24), color=(240, 240, 240))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    try:
        response = client.post(
            "/render",
            json={
                "input": {
                    "image": {
                        "content_type": "image/png",
                        "filename": "sample.png",
                        "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
                    },
                    "iou_threshold": 0.5,
                    "conf_threshold": 0.35,
                },
                "visualization": {"show_class_id": True, "show_conf": True},
                "request_id": "req-perception",
            },
        )

        body = response.get_json()
        result_image = Image.open(io.BytesIO(base64.b64decode(body["image"]["data"])))
        debug_image = Image.open(RENDER_DEBUG_PATH)

        assert response.status_code == 200
        assert body["status"] == "success"
        assert body["image"]["content_type"] == "image/png"
        assert result_image.size == (32, 24)
        assert debug_image.size == (32, 24)
    finally:
        if debug_backup is None:
            RENDER_DEBUG_PATH.unlink(missing_ok=True)
        else:
            RENDER_DEBUG_PATH.write_bytes(debug_backup)
