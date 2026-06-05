from __future__ import annotations

import json
import gradio as gr

from app import RESPONSIVE_SQUARE_MEDIA_CSS, build_app
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
    perception_resources_dir = tmp_path / "components" / "perception_demo" / "resources"
    perception_images_dir = perception_resources_dir / "images"
    perception_images_dir.mkdir(parents=True)
    (perception_resources_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "sample_image",
                    "name": "Sample Image",
                    "preview": "images/sample.png",
                    "data": "images/sample.png",
                    "content_type": "image/png",
                }
            ]
        ),
        encoding="utf-8",
    )
    (perception_images_dir / "sample.png").write_bytes(b"fake-png")
    path_planner_resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    path_planner_maps_dir = path_planner_resources_dir / "maps"
    path_planner_maps_dir.mkdir(parents=True)
    (path_planner_resources_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "warehouse_map",
                    "name": "Warehouse Map",
                    "data": "maps/warehouse.json",
                    "content_type": "array/list",
                    "shape": [3, 4],
                    "dtype": "uint8",
                }
            ]
        ),
        encoding="utf-8",
    )
    (path_planner_maps_dir / "warehouse.json").write_text(
        json.dumps([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]),
        encoding="utf-8",
    )
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


def test_build_app_adds_responsive_square_preview_css(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test Platform"),
            servers={},
        ),
        project_root=tmp_path,
    )

    build_app(ctx)

    assert "#json-demo-output-image" in RESPONSIVE_SQUARE_MEDIA_CSS
    assert ".image-container" in RESPONSIVE_SQUARE_MEDIA_CSS
    assert "display: block;" in RESPONSIVE_SQUARE_MEDIA_CSS
    assert "width: 100% !important;" in RESPONSIVE_SQUARE_MEDIA_CSS
    assert "aspect-ratio: 1 / 1" in RESPONSIVE_SQUARE_MEDIA_CSS
    assert "#path-planner-map-preview" not in RESPONSIVE_SQUARE_MEDIA_CSS
