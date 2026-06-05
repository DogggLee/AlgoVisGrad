from __future__ import annotations

import inspect
import json
from pathlib import Path

import gradio as gr
import numpy as np
from PIL import Image

from components.path_planner_demo.vis_window import build_path_planner_payload
from components.path_planner_demo.vis_window import (
    PathPlannerDemoVisWindow,
    PATH_PLANNER_DEMO_RESULT_SIZE,
    check_path_planner_demo_health,
    format_health_indicator,
    get_path_planner_map_dimensions,
    get_path_planner_map_preview,
    preview_path_planner_from_inputs,
    preview_path_planner_request,
    resolve_path_planner_map_payload,
    run_path_planner_render_from_inputs,
)
from utils.app_context import AppContext
from utils.config_utils import AppConfig, AppSettings


def test_build_path_planner_payload_uses_xy_coordinates_and_visualization_flags() -> None:
    map_payload = {
        "content_type": "array/list",
        "filename": "warehouse.json",
        "shape": [10, 20, 3],
        "dtype": "uint8",
        "data": [],
    }

    payload = build_path_planner_payload(
        map_payload=map_payload,
        start_x=1,
        start_y=2,
        goal_x=18,
        goal_y=8,
        inflation_radius=3,
        show_start=True,
        show_goal=True,
        show_path_cost=True,
        show_candidate_paths=False,
        show_inflation_area=True,
        request_id="req-path",
    )

    assert payload == {
        "input": {
            "map": map_payload,
            "start": [1, 2],
            "goal": [18, 8],
            "inflation_radius": 3,
        },
        "visualization": {
            "show_start": True,
            "show_goal": True,
            "show_path_cost": True,
            "show_candidate_paths": False,
            "show_inflation_area": True,
        },
        "request_id": "req-path",
    }


def test_path_planner_demo_vis_window_builds_inside_gradio_container(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = PathPlannerDemoVisWindow(
        window_id="path_planner_demo",
        title="Path Planner Demo",
        server_key="path_planner",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert components["example_selector"].label == "Map Example"
    assert components["map_preview"].label == "Selected Map Preview"
    assert components["map_preview"].elem_id == "path-planner-map-preview"
    assert components["uploaded_map"].label == "Upload Map File"
    assert "title_text" in components
    assert "health_indicator" in components
    assert "refresh_health_button" in components
    assert components["start_x"].value == 0
    assert components["start_y"].value == 0
    assert components["goal_x"].value == 1
    assert components["goal_y"].value == 1
    assert components["inflation_radius"].value == 1
    assert components["show_start"].value is True
    assert components["show_goal"].value is True
    assert components["show_path_cost"].value is True
    assert components["output_image"].elem_id == "path-planner-output-image"
    assert "output_image" in components
    assert "request_json" in components
    assert "response_json" in components


def test_get_path_planner_map_preview_draws_start_and_goal_markers(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "warehouse_map",
                    "name": "Warehouse Map",
                    "data": "maps/warehouse.json",
                    "content_type": "array/list",
                    "shape": [2, 3],
                    "dtype": "uint8",
                }
            ]
        ),
        encoding="utf-8",
    )
    (maps_dir / "warehouse.json").write_text(
        json.dumps([[0, 0, 0], [0, 0, 0]]),
        encoding="utf-8",
    )
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    preview = get_path_planner_map_preview(
        ctx,
        selected_map_id="warehouse_map",
        start_x=0,
        start_y=0,
        goal_x=2,
        goal_y=1,
    )

    assert preview is not None
    assert preview.size == (498, 332)
    start_pixel = preview.getpixel((0, 0))
    goal_pixel = preview.getpixel((preview.width - 1, preview.height - 1))
    assert start_pixel == (0, 200, 0)
    assert goal_pixel == (220, 0, 0)


def test_path_planner_demo_vis_window_loads_map_examples_and_slider_maximums(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "warehouse_map",
                    "name": "Warehouse Map",
                    "data": "maps/warehouse.json",
                    "content_type": "array/list",
                    "shape": [5, 7],
                    "dtype": "uint8",
                }
            ]
        ),
        encoding="utf-8",
    )
    (maps_dir / "warehouse.json").write_text(
        json.dumps([[0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 1], [0, 0, 0]]),
        encoding="utf-8",
    )
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = PathPlannerDemoVisWindow(
        window_id="path_planner_demo",
        title="Path Planner Demo",
        server_key="path_planner",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert components["example_selector"].choices == [("Warehouse Map", "warehouse_map")]
    assert components["start_x"].maximum == 6
    assert components["goal_x"].maximum == 6
    assert components["start_y"].maximum == 4
    assert components["goal_y"].maximum == 4
    assert components["goal_x"].value == 6
    assert components["goal_y"].value == 4


def test_path_planner_demo_vis_window_compacts_example_and_action_controls() -> None:
    source = inspect.getsource(PathPlannerDemoVisWindow.build)

    assert source.index('example_selector = gr.Dropdown(') < source.index('uploaded_map = gr.UploadButton(')
    assert 'scale=5' in source
    assert 'scale=1' in source
    assert source.index('inflation_radius = gr.Slider(') < source.index('preview_button = gr.Button("Preview", size="sm", scale=1, min_width=96)')
    assert source.index('preview_button = gr.Button("Preview", size="sm", scale=1, min_width=96)') < source.index('render_button = gr.Button("Send", size="sm", variant="primary", scale=1, min_width=96)')


def test_path_planner_demo_vis_window_uses_starter_template_comment_skeleton() -> None:
    source = inspect.getsource(PathPlannerDemoVisWindow.build)

    assert "Starter template title row" in source
    assert "Starter template input column" in source
    assert "Starter template render column" in source
    assert "Starter template debug row" in source
    assert "Starter template callback definitions" in source
    assert "Starter template event bindings and returned components" in source


def test_format_path_planner_demo_health_indicator_marks_online_green() -> None:
    assert format_health_indicator("online: ready") == "🟢 online"


def test_check_path_planner_demo_health_formats_state_and_message() -> None:
    class FakeHealthClient:
        def check(self, server_key: str):
            assert server_key == "path_planner"
            return type("Status", (), {"state": "offline", "message": "path_planner is offline"})()

    class FakeCtx:
        health_client = FakeHealthClient()

    assert check_path_planner_demo_health(FakeCtx(), "path_planner") == "offline: path_planner is offline"


def test_resolve_path_planner_map_payload_packs_selected_resource(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (maps_dir / "warehouse.json").write_text(
        json.dumps([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]),
        encoding="utf-8",
    )
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    payload = resolve_path_planner_map_payload(ctx=ctx, selected_map_id="warehouse_map")

    assert payload == {
        "content_type": "array/list",
        "filename": "warehouse.json",
        "shape": [3, 4],
        "dtype": "uint8",
        "data": [[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]],
    }


def test_resolve_path_planner_map_payload_packs_selected_npy_resource(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "warehouse_map",
                    "name": "Warehouse Map",
                    "data": "maps/warehouse.npy",
                    "content_type": "array/npy",
                    "shape": [3, 4],
                    "dtype": "uint8",
                }
            ]
        ),
        encoding="utf-8",
    )
    array = np.array([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]], dtype=np.uint8)
    np.save(maps_dir / "warehouse.npy", array)
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    payload = resolve_path_planner_map_payload(ctx=ctx, selected_map_id="warehouse_map")

    assert payload["content_type"] == "array/npy"
    assert payload["filename"] == "warehouse.npy"
    assert payload["shape"] == [3, 4]
    assert payload["dtype"] == "uint8"
    assert payload["data"]


def test_resolve_path_planner_map_payload_packs_uploaded_npy_file(tmp_path) -> None:
    array = np.array([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]], dtype=np.uint8)
    uploaded_path = tmp_path / "uploaded_map.npy"
    np.save(uploaded_path, array)
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    payload = resolve_path_planner_map_payload(
        ctx=ctx,
        selected_map_id=None,
        uploaded_map_path=str(uploaded_path),
    )

    assert payload["content_type"] == "array/npy"
    assert payload["filename"] == "uploaded_map.npy"
    assert payload["shape"] == [3, 4]
    assert payload["dtype"] == "uint8"
    assert payload["data"]


def test_preview_path_planner_request_returns_request_json() -> None:
    request_json = preview_path_planner_request(
        map_payload={
            "content_type": "array/list",
            "filename": "warehouse.json",
            "shape": [3, 4],
            "dtype": "uint8",
            "data": [[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]],
        },
        start_x=1,
        start_y=2,
        goal_x=3,
        goal_y=0,
        inflation_radius=2,
        show_start=True,
        show_goal=False,
        show_path_cost=True,
        show_candidate_paths=False,
        show_inflation_area=True,
        request_id="req-path-preview",
    )

    assert request_json["input"]["start"] == [1, 2]
    assert request_json["input"]["goal"] == [3, 0]
    assert request_json["visualization"] == {
        "show_start": True,
        "show_goal": False,
        "show_path_cost": True,
        "show_candidate_paths": False,
        "show_inflation_area": True,
    }
    assert request_json["request_id"] == "req-path-preview"


def test_preview_path_planner_from_inputs_resolves_map_and_returns_request_json(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (maps_dir / "warehouse.json").write_text(
        json.dumps([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]),
        encoding="utf-8",
    )
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    request_json = preview_path_planner_from_inputs(
        ctx=ctx,
        selected_map_id="warehouse_map",
        start_x=1,
        start_y=2,
        goal_x=3,
        goal_y=0,
        inflation_radius=2,
        show_start=True,
        show_goal=True,
        show_path_cost=False,
        show_candidate_paths=True,
        show_inflation_area=False,
        request_id="req-preview",
    )

    assert request_json["input"]["map"]["shape"] == [3, 4]
    assert request_json["input"]["start"] == [1, 2]
    assert request_json["input"]["goal"] == [3, 0]
    assert request_json["visualization"] == {
        "show_start": True,
        "show_goal": True,
        "show_path_cost": False,
        "show_candidate_paths": True,
        "show_inflation_area": False,
    }


def test_get_path_planner_map_dimensions_uses_selected_map_shape(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "warehouse_map",
                    "name": "Warehouse Map",
                    "data": "maps/warehouse.json",
                    "content_type": "array/list",
                    "shape": [6, 9],
                    "dtype": "uint8",
                }
            ]
        ),
        encoding="utf-8",
    )
    (maps_dir / "warehouse.json").write_text(json.dumps([[0] * 9] * 6), encoding="utf-8")
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    width, height = get_path_planner_map_dimensions(ctx=ctx, selected_map_id="warehouse_map")

    assert width == 9
    assert height == 6


class FakePathPlannerRenderClient:
    def __init__(self) -> None:
        self.calls = []

    def render_image_response(self, server_key, payload):
        self.calls.append((server_key, payload))
        return "image-result", {
            "status": "success",
            "image": {"content_type": "image/png", "data": "x" * 200},
            "meta": {"elapsed_ms": 11},
        }


class FakePathPlannerCtx:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.render_client = FakePathPlannerRenderClient()

    def component_resource_path(self, component_name, *parts):
        return self.project_root / "components" / component_name / "resources" / Path(*parts)


def test_run_path_planner_render_from_inputs_upscales_grid_result_image_for_display(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (maps_dir / "warehouse.json").write_text(
        json.dumps([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]),
        encoding="utf-8",
    )

    class FakeImageRenderClient:
        def __init__(self) -> None:
            self.calls = []

        def render_image_response(self, server_key, payload):
            self.calls.append((server_key, payload))
            return Image.new("RGB", (4, 3), color=(255, 255, 255)), {
                "status": "success",
                "image": {"content_type": "image/png", "data": "x" * 200},
                "meta": {"elapsed_ms": 11},
            }

    class FakeImageCtx(FakePathPlannerCtx):
        def __init__(self, project_root: Path) -> None:
            self.project_root = project_root
            self.render_client = FakeImageRenderClient()

    ctx = FakeImageCtx(tmp_path)

    image, status, request_json, response_json = run_path_planner_render_from_inputs(
        ctx=ctx,
        server_key="path_planner",
        selected_map_id="warehouse_map",
        start_x=1,
        start_y=2,
        goal_x=3,
        goal_y=0,
        inflation_radius=2,
        show_start=True,
        show_goal=False,
        show_path_cost=True,
        show_candidate_paths=True,
        show_inflation_area=False,
        request_id="req-render",
    )

    assert image.size == (500, 375)
    assert status == "Success. elapsed_ms=11"
    assert request_json["input"]["start"] == [1, 2]
    assert response_json["image"]["data"] == "x" * 200


def test_run_path_planner_render_from_inputs_calls_render_client_and_returns_outputs(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "path_planner_demo" / "resources"
    maps_dir = resources_dir / "maps"
    maps_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (maps_dir / "warehouse.json").write_text(
        json.dumps([[0, 1, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]),
        encoding="utf-8",
    )
    ctx = FakePathPlannerCtx(tmp_path)

    image, status, request_json, response_json = run_path_planner_render_from_inputs(
        ctx=ctx,
        server_key="path_planner",
        selected_map_id="warehouse_map",
        start_x=1,
        start_y=2,
        goal_x=3,
        goal_y=0,
        inflation_radius=2,
        show_start=True,
        show_goal=False,
        show_path_cost=True,
        show_candidate_paths=True,
        show_inflation_area=False,
        request_id="req-render",
    )

    assert image == "image-result"
    assert status == "Success. elapsed_ms=11"
    assert request_json["input"]["start"] == [1, 2]
    assert response_json["image"]["data"] == "x" * 200
    assert ctx.render_client.calls[0][0] == "path_planner"
    assert ctx.render_client.calls[0][1]["visualization"] == {
        "show_start": True,
        "show_goal": False,
        "show_path_cost": True,
        "show_candidate_paths": True,
        "show_inflation_area": False,
    }
