from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

from components.path_planner_demo.mock_server import create_path_planner_demo_mock_app


def test_path_planner_demo_mock_server_health_endpoint_reports_ok() -> None:
    app = create_path_planner_demo_mock_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_path_planner_demo_mock_server_render_endpoint_returns_base64_png() -> None:
    app = create_path_planner_demo_mock_app()
    client = app.test_client()

    response = client.post(
        "/render",
        json={
            "input": {
                "map": {
                    "content_type": "array/list",
                    "filename": "warehouse.json",
                    "shape": [4, 6],
                    "dtype": "uint8",
                    "data": [
                        [0, 0, 0, 0, 0, 0],
                        [0, 1, 1, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0],
                        [0, 0, 0, 0, 0, 0],
                    ],
                },
                "start": [0, 0],
                "goal": [5, 3],
                "inflation_radius": 1,
            },
            "visualization": {
                "show_start": True,
                "show_goal": True,
                "show_path_cost": True,
                "show_candidate_paths": True,
                "show_inflation_area": True,
            },
            "request_id": "req-path-planner",
        },
    )

    body = response.get_json()
    result_image = Image.open(io.BytesIO(base64.b64decode(body["image"]["data"])))

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["image"]["content_type"] == "image/png"
    assert result_image.size == (6, 4)



def test_path_planner_demo_mock_server_render_endpoint_accepts_npy_map_payload() -> None:
    app = create_path_planner_demo_mock_app()
    client = app.test_client()
    grid = np.array(
        [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )
    buffer = io.BytesIO()
    np.save(buffer, grid)

    response = client.post(
        "/render",
        json={
            "input": {
                "map": {
                    "content_type": "array/npy",
                    "filename": "warehouse.npy",
                    "shape": [3, 4],
                    "dtype": "uint8",
                    "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
                },
                "start": [0, 0],
                "goal": [3, 2],
                "inflation_radius": 1,
            },
            "visualization": {
                "show_start": True,
                "show_goal": True,
                "show_path_cost": False,
                "show_candidate_paths": False,
                "show_inflation_area": False,
            },
            "request_id": "req-path-planner-npy",
        },
    )

    body = response.get_json()
    result_image = Image.open(io.BytesIO(base64.b64decode(body["image"]["data"])))

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["image"]["content_type"] == "image/png"
    assert result_image.size == (4, 3)
