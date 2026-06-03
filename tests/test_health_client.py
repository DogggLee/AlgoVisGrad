from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from tests.helpers import run_test_server
from utils.config_utils import AppConfig, AppSettings, ServerSettings
from utils.health_client import HealthClient


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        body = json.dumps({"status": "ok", "name": "planner"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def test_health_client_reports_online_for_ok_health_response() -> None:
    with run_test_server(HealthHandler) as server:
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

        status = HealthClient(config).check("path_planner")

        assert status.state == "online"
        assert "planner" in status.message

def test_health_client_reports_offline_when_connection_fails() -> None:
    config = AppConfig(
        app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
        servers={
            "path_planner": ServerSettings(
                base_url="http://127.0.0.1:9",
                health_path="/health",
                render_path="/render",
                timeout_seconds=0.1,
            )
        },
    )

    status = HealthClient(config).check("path_planner")

    assert status.state == "offline"
    assert "path_planner" in status.message

class UnhealthyHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = json.dumps({"status": "error", "message": "not ready"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def test_health_client_reports_error_for_unhealthy_response() -> None:
    with run_test_server(UnhealthyHandler) as server:
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

        status = HealthClient(config).check("path_planner")

        assert status.state == "error"
        assert "unhealthy" in status.message

class HttpErrorHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(500)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def test_health_client_reports_error_for_http_error_response() -> None:
    with run_test_server(HttpErrorHealthHandler) as server:
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

        status = HealthClient(config).check("path_planner")

        assert status.state == "error"
        assert "health check failed" in status.message

