from __future__ import annotations

import base64
import io
import math
from typing import Any

from flask import Flask, jsonify, request
from PIL import Image, ImageDraw


Point = tuple[int, int]


def create_json_demo_mock_app() -> Flask:
    """Create the Flask mock server for the JSON demo algorithm service.

    Args:
        None.

    Returns:
        Flask application exposing `/health` and `/render` endpoints.
    """
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "name": "json_demo_mock", "version": "1.0.0"})

    @app.post("/render")
    def render():
        request_payload = request.get_json(force=True)
        image = render_json_demo_image(
            payload=request_payload["input"]["payload"],
            show_cost=bool(request_payload.get("visualization", {}).get("show_cost", False)),
        )
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


def main() -> None:
    """Run the JSON demo mock Flask server on the default demo endpoint.

    Args:
        None.

    Returns:
        None. This function blocks while the Flask development server is running.
    """
    create_json_demo_mock_app().run(host="127.0.0.1", port=5003)


def render_json_demo_image(payload: dict[str, Any], show_cost: bool) -> Image.Image:
    """Render the JSON demo payload into a visualization image.

    Args:
        payload: JSON object with `group1`, `group2`, and `map_size`; points use
            `[x, y]` pixel coordinates and `map_size` uses `[H, W]`.
        show_cost: Whether to draw nearest-neighbor line length labels.

    Returns:
        RGB PIL image with group1 red points, group2 blue points, and nearest
        group1-to-group2 connections in green.
    """
    height, width = payload["map_size"]
    group1 = [_to_point(point) for point in payload["group1"]]
    group2 = [_to_point(point) for point in payload["group2"]]

    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    for point in group1:
        nearest, distance = _nearest_point(point, group2)
        draw.line([point, nearest], fill=(0, 180, 0), width=1)
        if show_cost:
            midpoint = ((point[0] + nearest[0]) // 2, (point[1] + nearest[1]) // 2)
            draw.text(midpoint, f"{distance:.1f}", fill=(0, 0, 0))

    for point in group1:
        _draw_point(draw, point, fill=(255, 0, 0))

    for point in group2:
        _draw_point(draw, point, fill=(0, 0, 255))

    return image


def _to_point(value: list[int] | tuple[int, int]) -> Point:
    """Convert a two-element coordinate value into an integer point tuple.

    Args:
        value: Two-element `[x, y]` or `(x, y)` coordinate.

    Returns:
        Integer `(x, y)` point tuple.
    """
    return int(value[0]), int(value[1])


def _nearest_point(point: Point, candidates: list[Point]) -> tuple[Point, float]:
    """Find the Euclidean nearest point from a candidate list.

    Args:
        point: Source `(x, y)` point.
        candidates: Candidate `(x, y)` points to compare against.

    Returns:
        Tuple of nearest candidate point and Euclidean distance.
    """
    nearest = min(candidates, key=lambda candidate: _distance(point, candidate))
    return nearest, _distance(point, nearest)


def _distance(a: Point, b: Point) -> float:
    """Compute Euclidean distance between two image points.

    Args:
        a: First `(x, y)` point.
        b: Second `(x, y)` point.

    Returns:
        Euclidean pixel distance.
    """
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _draw_point(draw: ImageDraw.ImageDraw, point: Point, fill: tuple[int, int, int]) -> None:
    """Draw a small filled circular marker centered on a point.

    Args:
        draw: PIL drawing context.
        point: Center `(x, y)` point.
        fill: RGB marker color.

    Returns:
        None.
    """
    x, y = point
    radius = 3
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill)


if __name__ == "__main__":
    main()
