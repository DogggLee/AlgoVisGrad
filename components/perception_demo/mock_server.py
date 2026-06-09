from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from PIL import Image, ImageDraw

RENDER_DEBUG_PATH = Path(__file__).resolve().with_name("render.png")


def create_perception_demo_mock_app() -> Flask:
    """Create the Flask mock server for the perception demo algorithm service.

    Args:
        None.

    Returns:
        Flask application exposing `/health` and `/render` endpoints.
    """
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "name": "perception_demo_mock", "version": "1.0.0"})

    @app.post("/render")
    def render():
        request_payload = request.get_json(force=True)
        image_payload = request_payload["input"]["image"]
        image = render_perception_demo_image(
            image_payload=image_payload,
            show_class_id=bool(request_payload.get("visualization", {}).get("show_class_id", False)),
            show_conf=bool(request_payload.get("visualization", {}).get("show_conf", False)),
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


def render_perception_demo_image(
    image_payload: dict[str, Any],
    show_class_id: bool,
    show_conf: bool,
) -> Image.Image:
    """Render a simple perception visualization on top of the input image.

    Args:
        image_payload: Packed image payload with base64 data.
        show_class_id: Whether to draw a class-id label.
        show_conf: Whether to draw a confidence label.

    Returns:
        RGB PIL image containing simple mock detection overlays.
    """
    image_bytes = base64.b64decode(image_payload["data"])
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    left = max(width // 6, 1)
    top = max(height // 6, 1)
    right = max(width * 5 // 6, left + 1)
    bottom = max(height * 5 // 6, top + 1)

    draw.rectangle([left, top, right, bottom], outline=(255, 80, 0), width=2)
    label_parts = []
    if show_class_id:
        label_parts.append("class=1")
    if show_conf:
        label_parts.append("conf=0.92")
    if label_parts:
        draw.text((left, max(top - 12, 0)), " ".join(label_parts), fill=(0, 0, 0))

    return image


def main() -> None:
    """Run the perception demo mock Flask server on the default demo endpoint.

    Args:
        None.

    Returns:
        None. This function blocks while the Flask development server is running.
    """
    create_perception_demo_mock_app().run(host="127.0.0.1", port=5001)


if __name__ == "__main__":
    main()
