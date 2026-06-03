from __future__ import annotations

import base64
import io
from typing import Any
from urllib.parse import urljoin

import requests
from PIL import Image

from utils.config_utils import AppConfig


class RenderRequestError(Exception):
    """Raised when a render request cannot produce a successful image response.

    Args:
        message: Human-readable description of the render request failure.

    Returns:
        Exception instance carrying the normalized render error message.
    """


class RenderClient:
    def __init__(self, config: AppConfig) -> None:
        """Create a render client backed by platform server configuration.

        Args:
            config: Runtime config containing render endpoint definitions.
        """
        self._config = config

    def render_image(
        self, server_key: str, payload: dict[str, Any]
    ) -> tuple[Image.Image, dict[str, Any]]:
        """Send a render request and decode the returned base64 image.

        Args:
            server_key: Key in config.servers identifying the algorithm server.
            payload: Render request body using the input/visualization/request_id protocol.

        Returns:
            A tuple of decoded PIL image and response metadata dictionary.
        """
        image, response_payload = self.render_image_response(server_key, payload)
        return image, response_payload.get("meta", {})

    def render_image_response(
        self, server_key: str, payload: dict[str, Any]
    ) -> tuple[Image.Image, dict[str, Any]]:
        """Send a render request and return the decoded image plus full response JSON.

        Args:
            server_key: Key in config.servers identifying the algorithm server.
            payload: Render request body using the input/visualization/request_id protocol.

        Returns:
            A tuple of decoded PIL image and the full JSON response payload.
        """
        server = self._config.servers[server_key]
        url = urljoin(server.base_url.rstrip("/") + "/", server.render_path.lstrip("/"))
        try:
            response = requests.post(url, json=payload, timeout=server.timeout_seconds)
            response.raise_for_status()
            response_payload = response.json()

            if response_payload.get("status") == "error":
                error = response_payload.get("error", {})
                message = error.get("message", "Algorithm server returned an error")
                raise RenderRequestError(str(message))

            image_payload = response_payload["image"]
            image_bytes = base64.b64decode(image_payload["data"])
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except RenderRequestError:
            raise
        except requests.RequestException as exc:
            raise RenderRequestError(str(exc)) from exc
        except (KeyError, ValueError, TypeError) as exc:
            raise RenderRequestError(f"Invalid render response: {exc}") from exc

        return image, response_payload
