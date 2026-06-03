from __future__ import annotations

import json
import gradio as gr

from app import build_app
from utils.app_context import AppContext
from utils.config_utils import AppConfig, AppSettings


def test_build_app_returns_gradio_blocks(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test Platform"),
            servers={},
        ),
        project_root=tmp_path,
    )

    app = build_app(ctx)

    assert isinstance(app, gr.Blocks)

def test_build_app_embeds_json_demo_window_with_resource_default(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "json_demo" / "resources"
    inputs_dir = resources_dir / "inputs"
    inputs_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "two_groups",
                    "name": "Two Groups",
                    "data": "inputs/two_groups.json",
                    "content_type": "application/json",
                }
            ]
        ),
        encoding="utf-8",
    )
    (inputs_dir / "two_groups.json").write_text(
        json.dumps({"group1": [[1, 2]], "group2": [[3, 4]], "map_size": [8, 9]}),
        encoding="utf-8",
    )
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test Platform"),
            servers={},
        ),
        project_root=tmp_path,
    )

    app = build_app(ctx)

    assert isinstance(app, gr.Blocks)

