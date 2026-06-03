from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppSettings:
    host: str
    port: int
    title: str


@dataclass(frozen=True)
class ServerSettings:
    base_url: str
    health_path: str
    render_path: str
    timeout_seconds: float


@dataclass(frozen=True)
class AppConfig:
    app: AppSettings
    servers: dict[str, ServerSettings]


def load_config(path: str | Path) -> AppConfig:
    """Load platform runtime configuration from a YAML file.

    Args:
        path: Filesystem path to the YAML configuration file.

    Returns:
        AppConfig containing launch settings and server endpoint settings.
    """
    config_path = Path(path)
    raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    app = _parse_app_settings(raw_config.get("app", {}))
    servers = {
        key: _parse_server_settings(value)
        for key, value in raw_config.get("servers", {}).items()
    }

    return AppConfig(app=app, servers=servers)


def _parse_app_settings(raw_app: dict[str, Any]) -> AppSettings:
    return AppSettings(
        host=str(raw_app["host"]),
        port=int(raw_app["port"]),
        title=str(raw_app["title"]),
    )


def _parse_server_settings(raw_server: dict[str, Any]) -> ServerSettings:
    return ServerSettings(
        base_url=str(raw_server["base_url"]),
        health_path=str(raw_server["health_path"]),
        render_path=str(raw_server["render_path"]),
        timeout_seconds=float(raw_server["timeout_seconds"]),
    )
