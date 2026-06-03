from __future__ import annotations

import base64
import io
import json
import pytest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from PIL import Image

from utils.config_utils import AppConfig, AppSettings, ServerSettings
from utils.render_client import RenderClient, RenderRequestError


class RenderHandler(BaseHTTPRequestHandler):
    received_payload: dict | None = None

    def do_POST(self) -> None:
        if self.path != "/render":
            self.send_response(404)
            self.end_headers()
            return

        body = self.rfile.read(int(self.headers["Content-Length"]))
        RenderHandler.received_payload = json.loads(body.decode("utf-8"))

        image = Image.new("RGB", (2, 3), color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        response_body = json.dumps(
            {
                "status": "success",
                "image": {
                    "content_type": "image/png",
                    "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
                },
                "meta": {"elapsed_ms": 12},
            }
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format: str, *args: object) -> None:
        return


def test_render_client_posts_payload_and_decodes_image() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), RenderHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        config = AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={
                "path_planner": ServerSettings(
                    base_url=f"http://{host}:{port}",
                    health_path="/health",
                    render_path="/render",
                    timeout_seconds=1,
                )
            },
        )
        payload = {
            "input": {"start": [1, 2]},
            "visualization": {"show_path_cost": True},
            "request_id": "req-test",
        }

        image, meta = RenderClient(config).render_image("path_planner", payload)

        assert RenderHandler.received_payload == payload
        assert image.size == (2, 3)
        assert meta == {"elapsed_ms": 12}
    finally:
        server.shutdown()
        server.server_close()

def test_render_client_can_return_decoded_image_and_full_response_payload() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), RenderHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        config = AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={
                "path_planner": ServerSettings(
                    base_url=f"http://{host}:{port}",
                    health_path="/health",
                    render_path="/render",
                    timeout_seconds=1,
                )
            },
        )
        payload = {"input": {}, "visualization": {}, "request_id": "req-test"}

        image, response_payload = RenderClient(config).render_image_response("path_planner", payload)

        assert image.size == (2, 3)
        assert response_payload["status"] == "success"
        assert response_payload["image"]["content_type"] == "image/png"
        assert response_payload["meta"] == {"elapsed_ms": 12}
    finally:
        server.shutdown()
        server.server_close()

class ErrorRenderHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        response_body = json.dumps(
            {
                "status": "error",
                "error": {"code": "INVALID_INPUT", "message": "bad payload"},
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format: str, *args: object) -> None:
        return


def test_render_client_raises_platform_error_for_algorithm_error_response() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), ErrorRenderHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        config = AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={
                "json_demo": ServerSettings(
                    base_url=f"http://{host}:{port}",
                    health_path="/health",
                    render_path="/render",
                    timeout_seconds=1,
                )
            },
        )

        with pytest.raises(RenderRequestError, match="bad payload"):
            RenderClient(config).render_image_response(
                "json_demo", {"input": {}, "visualization": {}, "request_id": "req-error"}
            )
    finally:
        server.shutdown()
        server.server_close()

def test_render_client_wraps_connection_failures_in_platform_error() -> None:
    config = AppConfig(
        app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
        servers={
            "json_demo": ServerSettings(
                base_url="http://127.0.0.1:9",
                health_path="/health",
                render_path="/render",
                timeout_seconds=0.1,
            )
        },
    )

    with pytest.raises(RenderRequestError):
        RenderClient(config).render_image_response(
            "json_demo", {"input": {}, "visualization": {}, "request_id": "req-connection"}
        )

