from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import numpy as np
from flask import Flask, jsonify, request
from PIL import Image, ImageDraw

RENDER_DEBUG_PATH = Path(__file__).resolve().with_name("render.png")


def create_path_planner_demo_mock_app() -> Flask:
    """Create the Flask mock server for the path planner demo algorithm service.

    Args:
        None.

    Returns:
        Flask application exposing `/health` and `/render` endpoints.
    """
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "name": "path_planner_demo_mock", "version": "1.0.0"})

    @app.post("/render")
    def render():
        request_payload = request.get_json(force=True)
        image = render_path_planner_demo_image(
            map_payload=request_payload["input"]["map"],
            start=request_payload["input"]["start"],
            goal=request_payload["input"]["goal"],
            show_start=bool(request_payload.get("visualization", {}).get("show_start", False)),
            show_goal=bool(request_payload.get("visualization", {}).get("show_goal", False)),
            show_path_cost=bool(request_payload.get("visualization", {}).get("show_path_cost", False)),
            show_candidate_paths=bool(request_payload.get("visualization", {}).get("show_candidate_paths", False)),
            show_inflation_area=bool(request_payload.get("visualization", {}).get("show_inflation_area", False)),
        )
        image.save(RENDER_DEBUG_PATH, format="PNG")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return jsonify(
            {
                "status": "success",
                "image": {
                    "content_type": "image/png",
                    "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
                },
                "meta": {"request_id": request_payload.get("request_id")},
            }
        )

    return app


def decode_path_planner_demo_map_grid(map_payload: dict[str, Any]) -> np.ndarray:
    """Decode the packed map payload into a 2D numpy grid.

    Args:
        map_payload: Packed map payload containing `content_type` and serialized map data.

    Returns:
        Two-dimensional numpy array representing the occupancy grid.
    """
    content_type = str(map_payload.get("content_type", "array/list"))

    if content_type == "array/npy":
        data = base64.b64decode(map_payload["data"])
        grid = np.load(io.BytesIO(data), allow_pickle=False)
        return np.asarray(grid)

    return np.asarray(map_payload["data"])


def render_path_planner_demo_image(
    map_payload: dict[str, Any],
    start: list[int] | tuple[int, int],
    goal: list[int] | tuple[int, int],
    show_start: bool,
    show_goal: bool,
    show_path_cost: bool,
    show_candidate_paths: bool,
    show_inflation_area: bool,
) -> Image.Image:
    """Render a simple path planner visualization from the map payload.

    Args:
        map_payload: Packed map payload with `array/list` or `array/npy` data.
        start: Start point encoded as `[x, y]`.
        goal: Goal point encoded as `[x, y]`.
        show_start: Whether to draw the start marker.
        show_goal: Whether to draw the goal marker.
        show_path_cost: Whether to draw a path cost label.
        show_candidate_paths: Whether to draw a faint candidate line.
        show_inflation_area: Whether to tint obstacle neighbors.

    Returns:
        RGB PIL image whose size matches the map width and height.
    """
    grid = decode_path_planner_demo_map_grid(map_payload)
    height = int(grid.shape[0])
    width = int(grid.shape[1]) if grid.ndim >= 2 and grid.shape[0] else 1
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            if int(value):
                image.putpixel((x, y), (40, 40, 40))
                if show_inflation_area:
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= nx < width and 0 <= ny < height and image.getpixel((nx, ny)) == (255, 255, 255):
                            image.putpixel((nx, ny), (255, 235, 180))

    start_point = (int(start[0]), int(start[1]))
    goal_point = (int(goal[0]), int(goal[1]))
    if show_candidate_paths:
        draw.line([start_point, (start_point[0], goal_point[1])], fill=(180, 180, 255), width=1)
    draw.line([start_point, goal_point], fill=(0, 160, 0), width=1)

    if show_start:
        image.putpixel(start_point, (0, 200, 0))
    if show_goal:
        image.putpixel(goal_point, (220, 0, 0))
    if show_path_cost:
        draw.text((0, 0), f"cost={abs(goal_point[0] - start_point[0]) + abs(goal_point[1] - start_point[1])}", fill=(0, 0, 0))

    return image


def main() -> None:
    """Run the path planner demo mock Flask server on the default demo endpoint.

    Args:
        None.

    Returns:
        None. This function blocks while the Flask development server is running.
    """
    create_path_planner_demo_mock_app().run(host="127.0.0.1", port=5002)


if __name__ == "__main__":
    main()
