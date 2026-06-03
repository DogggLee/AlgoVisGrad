from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any


def load_manifest(resources_dir: str | Path) -> list[dict[str, Any]]:
    """Load resource manifest items from a component resources directory.

    Args:
        resources_dir: Directory containing a `manifest.json` file.

    Returns:
        List of manifest item dictionaries describing preview/data resources.
    """
    manifest_path = Path(resources_dir) / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def pack_resource(resource_root: str | Path, item: dict[str, Any]) -> dict[str, Any]:
    """Pack one manifest resource item into the standard request payload shape.

    Args:
        resource_root: Directory that manifest-relative resource paths are resolved from.
        item: Manifest item containing at least `data` and `content_type`; array
            resources may also include `shape` and `dtype`.

    Returns:
        A payload dictionary suitable for placing under the render request `input`,
        with file bytes base64-encoded for image resources and raw JSON values for
        `array/list` resources.
    """
    content_type = str(item["content_type"])
    data_path = Path(resource_root) / str(item["data"])

    if content_type in {"image/png", "image/jpeg"}:
        return {
            "content_type": content_type,
            "filename": data_path.name,
            "data": base64.b64encode(data_path.read_bytes()).decode("ascii"),
        }

    if content_type == "array/list":
        return {
            "content_type": content_type,
            "filename": data_path.name,
            "shape": item.get("shape"),
            "dtype": item.get("dtype"),
            "data": json.loads(data_path.read_text(encoding="utf-8")),
        }

    if content_type == "array/npy":
        return {
            "content_type": content_type,
            "filename": data_path.name,
            "shape": item.get("shape"),
            "dtype": item.get("dtype"),
            "data": base64.b64encode(data_path.read_bytes()).decode("ascii"),
        }

    raise ValueError(f"Unsupported content_type: {content_type}")
