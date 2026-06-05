from __future__ import annotations

import inspect
import json
import gradio as gr

from components.json_demo.vis_window import (
    JsonDemoVisWindow,
    build_json_demo_payload,
    preview_json_demo_request,
    run_json_demo_render,
    load_json_demo_example,
    load_json_demo_examples,
    parse_json_demo_input,
    JSON_DEMO_EDITOR_LINES,
    check_json_demo_health,
    format_health_indicator,
)
from utils.app_context import AppContext
from utils.config_utils import AppConfig, AppSettings


def test_build_json_demo_payload_uses_standard_render_request_shape() -> None:
    payload = build_json_demo_payload(
        user_payload={"nodes": [1, 2], "edges": []},
        show_cost=True,
        request_id="req-json",
    )

    assert payload == {
        "input": {
            "payload": {"nodes": [1, 2], "edges": []},
        },
        "visualization": {
            "show_cost": True,
        },
        "request_id": "req-json",
    }

def test_json_demo_vis_window_builds_inside_gradio_container(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = JsonDemoVisWindow(
        window_id="json_demo",
        title="JSON Demo",
        server_key="json_demo",
    )

    with gr.Blocks():
        build_result = window.build(ctx)

    assert build_result is not None
    assert build_result["output_image"].elem_id == "json-demo-output-image"

def test_preview_json_demo_request_returns_summary_and_full_json_text() -> None:
    summary, full_text = preview_json_demo_request(
        user_payload={"blob": "x" * 40},
        show_cost=False,
        request_id="req-preview",
        max_string_length=10,
    )

    assert summary["input"]["payload"]["blob"] == "x" * 40
    assert '"request_id": "req-preview"' in full_text
    assert '"blob": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' in full_text

def test_json_demo_build_exposes_request_and_response_json_outputs(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = JsonDemoVisWindow(
        window_id="json_demo",
        title="JSON Demo",
        server_key="json_demo",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert "request_json" in components
    assert "response_json" in components
    assert "request_text" not in components


def test_json_demo_vis_window_uses_starter_template_comment_skeleton() -> None:
    source = inspect.getsource(JsonDemoVisWindow.build)

    assert "Starter template title row" in source
    assert "Starter template input column" in source
    assert "Starter template render column" in source
    assert "Starter template debug row" in source
    assert "Starter template callback definitions" in source
    assert "Starter template event bindings and returned components" in source

class FakeRenderClient:
    def __init__(self) -> None:
        self.calls = []

    def render_image_response(self, server_key, payload):
        self.calls.append((server_key, payload))
        return "image-result", {"status": "success", "image": {"content_type": "image/png", "data": "x" * 40}, "meta": {"elapsed_ms": 7}}


class FakeCtx:
    def __init__(self) -> None:
        self.render_client = FakeRenderClient()


def test_run_json_demo_render_calls_render_client_and_returns_ui_outputs() -> None:
    ctx = FakeCtx()

    image, status, request_json, response_json = run_json_demo_render(
        ctx=ctx,
        server_key="json_demo",
        user_payload={"cost": "x" * 40},
        show_cost=True,
        request_id="req-render",
        max_string_length=10,
    )

    assert image == "image-result"
    assert status == "Success. elapsed_ms=7"
    assert request_json["input"]["payload"]["cost"] == "x" * 40
    assert response_json["image"]["data"] == "<base64 length=40>"
    assert ctx.render_client.calls[0][0] == "json_demo"
    assert ctx.render_client.calls[0][1]["visualization"] == {"show_cost": True}

def test_load_json_demo_example_reads_payload_from_resources(tmp_path) -> None:
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
        json.dumps(
            {
                "group1": [[1, 2], [3, 4]],
                "group2": [[5, 6]],
                "map_size": [10, 20],
            }
        ),
        encoding="utf-8",
    )
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    payload = load_json_demo_example(ctx)

    assert payload == {
        "group1": [[1, 2], [3, 4]],
        "group2": [[5, 6]],
        "map_size": [10, 20],
    }

def test_json_demo_vis_window_starts_empty_and_exposes_resource_selector(tmp_path) -> None:
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
    expected = {"group1": [[1, 2]], "group2": [[3, 4]], "map_size": [8, 9]}
    (inputs_dir / "two_groups.json").write_text(json.dumps(expected), encoding="utf-8")
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = JsonDemoVisWindow(
        window_id="json_demo",
        title="JSON Demo",
        server_key="json_demo",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert components["json_input"].value == "{}"
    assert components["example_selector"].choices == [("Two Groups", "two_groups")]
    assert components["json_input"].interactive is True

def test_load_json_demo_examples_reads_selectable_resource_list(tmp_path) -> None:
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
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    examples = load_json_demo_examples(ctx)
    payload = load_json_demo_example(ctx, example_id="two_groups")

    assert examples == [{"id": "two_groups", "name": "Two Groups"}]
    assert payload == {"group1": [[1, 2]], "group2": [[3, 4]], "map_size": [8, 9]}

def test_parse_json_demo_input_accepts_editable_json_text() -> None:
    payload = parse_json_demo_input(
        '{"group1": [[1, 2]], "group2": [[3, 4]], "map_size": [8, 9]}'
    )

    assert payload == {"group1": [[1, 2]], "group2": [[3, 4]], "map_size": [8, 9]}

def test_json_demo_layout_uses_compact_top_controls_and_matching_result_height(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = JsonDemoVisWindow(
        window_id="json_demo",
        title="JSON Demo",
        server_key="json_demo",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert components["preview_button"].size == "sm"
    assert components["render_button"].size == "sm"
    assert components["json_input"].lines == JSON_DEMO_EDITOR_LINES
    assert components["output_image"].elem_id == "json-demo-output-image"

class FailingRenderClient:
    def render_image_response(self, server_key, payload):
        raise RuntimeError("server unavailable")


class FailingCtx:
    def __init__(self) -> None:
        self.render_client = FailingRenderClient()


def test_run_json_demo_render_returns_error_outputs_when_render_fails() -> None:
    image, status, request_json, response_json = run_json_demo_render(
        ctx=FailingCtx(),
        server_key="json_demo",
        user_payload={"group1": [], "group2": [], "map_size": [10, 10]},
        show_cost=False,
        request_id="req-error",
    )

    assert image is None
    assert status == "Error: server unavailable"
    assert request_json["request_id"] == "req-error"
    assert response_json == {
        "status": "error",
        "error": {"message": "server unavailable"},
    }

class FakeHealthClient:
    def __init__(self) -> None:
        self.calls = []

    def check(self, server_key):
        self.calls.append(server_key)
        return type("Status", (), {"state": "online", "message": "json server is online"})()


class HealthCtx:
    def __init__(self) -> None:
        self.health_client = FakeHealthClient()


def test_check_json_demo_health_returns_display_text() -> None:
    ctx = HealthCtx()

    text = check_json_demo_health(ctx, "json_demo")

    assert text == "online: json server is online"
    assert ctx.health_client.calls == ["json_demo"]

def test_json_demo_build_checks_initial_health_status(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
        health_client=FakeHealthClient(),
    )
    window = JsonDemoVisWindow(
        window_id="json_demo",
        title="JSON Demo",
        server_key="json_demo",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert components["title_text"].value == "## JSON Demo"
    assert components["health_indicator"].value == "🟢 online"
    assert components["refresh_health_button"].value == "↻"
    assert components["refresh_health_button"].size == "sm"
    assert ctx.health_client.calls == ["json_demo"]

def test_format_json_demo_health_indicator_uses_green_for_online_and_red_otherwise() -> None:
    online_text = format_health_indicator("online: json server is online")
    offline_text = format_health_indicator("offline: json server is offline")

    assert online_text == "🟢 online"
    assert offline_text == "🔴 offline"

def test_run_json_demo_render_returns_error_outputs_for_invalid_json_text() -> None:
    image, status, request_json, response_json = run_json_demo_render(
        ctx=FakeCtx(),
        server_key="json_demo",
        user_payload="{bad json",
        show_cost=True,
        request_id="req-invalid-json",
    )

    assert image is None
    assert status.startswith("Error: invalid JSON input")
    assert request_json == {
        "status": "error",
        "error": {"message": "invalid JSON input"},
        "request_id": "req-invalid-json",
    }
    assert response_json == {
        "status": "error",
        "error": {"message": "invalid JSON input"},
    }

def test_preview_json_demo_request_returns_error_for_invalid_json_text() -> None:
    summary, full_text = preview_json_demo_request(
        user_payload="{bad json",
        show_cost=False,
        request_id="req-preview-error",
    )

    assert summary == {
        "status": "error",
        "error": {"message": "invalid JSON input"},
        "request_id": "req-preview-error",
    }
    assert '"status": "error"' in full_text
