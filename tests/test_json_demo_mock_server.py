from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, ImageChops

from components.json_demo.mock_server import RENDER_DEBUG_PATH, create_json_demo_mock_app, render_json_demo_image


def test_render_json_demo_image_draws_group_points_and_nearest_connection() -> None:
    image = render_json_demo_image(
        payload={
            "group1": [[10, 10]],
            "group2": [[30, 10], [45, 40]],
            "map_size": [50, 60],
        },
        show_cost=False,
    )

    assert image.size == (60, 50)
    assert image.getpixel((10, 10)) == (255, 0, 0)
    assert image.getpixel((30, 10)) == (0, 0, 255)
    assert image.getpixel((20, 10)) == (0, 180, 0)


def test_render_json_demo_image_adds_cost_text_when_requested() -> None:
    payload = {
        "group1": [[10, 10]],
        "group2": [[30, 10]],
        "map_size": [50, 60],
    }

    without_cost = render_json_demo_image(payload=payload, show_cost=False)
    with_cost = render_json_demo_image(payload=payload, show_cost=True)

    assert ImageChops.difference(with_cost, without_cost).getbbox() is not None

def test_json_demo_mock_server_health_endpoint_reports_ok() -> None:
    app = create_json_demo_mock_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_json_demo_mock_server_render_endpoint_returns_base64_png() -> None:
    app = create_json_demo_mock_app()
    client = app.test_client()
    debug_backup = RENDER_DEBUG_PATH.read_bytes() if RENDER_DEBUG_PATH.exists() else None

    try:
        response = client.post(
            "/render",
            json={
                "input": {
                    "payload": {
                        "group1": [[10, 10]],
                        "group2": [[30, 10]],
                        "map_size": [50, 60],
                    }
                },
                "visualization": {"show_cost": True},
                "request_id": "req-test",
            },
        )

        body = response.get_json()
        image = Image.open(io.BytesIO(base64.b64decode(body["image"]["data"])))
        debug_image = Image.open(RENDER_DEBUG_PATH)

        assert response.status_code == 200
        assert body["status"] == "success"
        assert body["image"]["content_type"] == "image/png"
        assert image.size == (60, 50)
        assert debug_image.size == (60, 50)
    finally:
        if debug_backup is None:
            RENDER_DEBUG_PATH.unlink(missing_ok=True)
        else:
            RENDER_DEBUG_PATH.write_bytes(debug_backup)

def test_json_demo_mock_server_render_returns_error_for_missing_required_fields() -> None:
    app = create_json_demo_mock_app()
    client = app.test_client()

    response = client.post(
        "/render",
        json={
            "input": {"payload": {"group1": [[1, 2]], "map_size": [10, 10]}},
            "visualization": {"show_cost": False},
            "request_id": "req-missing",
        },
    )

    body = response.get_json()

    assert response.status_code == 200
    assert body["status"] == "error"
    assert "group2" in body["error"]["message"]


def test_json_demo_mock_server_render_returns_error_for_out_of_bounds_points() -> None:
    app = create_json_demo_mock_app()
    client = app.test_client()

    response = client.post(
        "/render",
        json={
            "input": {
                "payload": {
                    "group1": [[11, 2]],
                    "group2": [[3, 4]],
                    "map_size": [10, 10],
                }
            },
            "visualization": {"show_cost": False},
            "request_id": "req-oob",
        },
    )

    body = response.get_json()

    assert response.status_code == 200
    assert body["status"] == "error"
    assert "out of bounds" in body["error"]["message"]
