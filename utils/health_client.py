from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urljoin

import requests

from utils.config_utils import AppConfig


HealthState = Literal["online", "offline", "timeout", "error", "unknown"]


@dataclass(frozen=True)
class ServerStatus:
    state: HealthState
    message: str


class HealthClient:
    def __init__(self, config: AppConfig) -> None:
        """Create a health client backed by platform server configuration.

        Args:
            config: Runtime config containing server endpoint definitions.
        """
        self._config = config

    def check(self, server_key: str) -> ServerStatus:
        """Check one configured algorithm server health endpoint.

        Args:
            server_key: Key in config.servers identifying the algorithm server.

        Returns:
            ServerStatus describing the observed service state and message.
        """
        server = self._config.servers[server_key]
        url = urljoin(server.base_url.rstrip("/") + "/", server.health_path.lstrip("/"))

        try:
            response = requests.get(url, timeout=server.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.Timeout:
            return ServerStatus(state="timeout", message=f"{server_key} health check timed out")
        except requests.ConnectionError:
            return ServerStatus(state="offline", message=f"{server_key} is offline")
        except requests.RequestException as exc:
            return ServerStatus(state="error", message=f"{server_key} health check failed: {exc}")
        except ValueError as exc:
            return ServerStatus(state="error", message=f"{server_key} returned invalid health JSON: {exc}")

        if payload.get("status") == "ok":
            name = payload.get("name", server_key)
            return ServerStatus(state="online", message=f"{name} is online")

        return ServerStatus(state="error", message=f"{server_key} returned unhealthy status: {payload}")
