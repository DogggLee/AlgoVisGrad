from __future__ import annotations

import json
from pathlib import Path
import gradio as gr

from components.perception_demo.vis_window import (
    PerceptionDemoVisWindow,
    build_perception_payload,
    preview_perception_request,
    resolve_perception_image_payload,
    preview_perception_from_inputs,
    run_perception_render_from_inputs,
)
from utils.app_context import AppContext
from utils.config_utils import AppConfig, AppSettings


def test_build_perception_payload_uses_thresholds_and_visualization_flags() -> None:
    image_payload = {
        "content_type": "image/jpeg",
        "filename": "street.jpg",
        "data": "base64-image",
    }

    payload = build_perception_payload(
        image_payload=image_payload,
        iou_threshold=0.5,
        conf_threshold=0.35,
        show_class_id=True,
        show_conf=False,
        request_id="req-perception",
    )

    assert payload == {
        "input": {
            "image": image_payload,
            "iou_threshold": 0.5,
            "conf_threshold": 0.35,
        },
        "visualization": {
            "show_class_id": True,
            "show_conf": False,
        },
        "request_id": "req-perception",
    }

def test_perception_demo_vis_window_builds_inside_gradio_container(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = PerceptionDemoVisWindow(
        window_id="perception_demo",
        title="Perception Demo",
        server_key="perception",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert components["image_selector"].label == "Image Example"
    assert components["iou_threshold"].value == 0.5
    assert components["conf_threshold"].value == 0.35
    assert components["show_class_id"].value is True
    assert components["show_conf"].value is True
    assert "output_image" in components
    assert "request_json" in components
    assert "response_json" in components

def test_perception_demo_vis_window_loads_image_examples_from_resources(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "perception_demo" / "resources"
    images_dir = resources_dir / "images"
    images_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (images_dir / "sample.png").write_bytes(b"not-used-by-build")
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )
    window = PerceptionDemoVisWindow(
        window_id="perception_demo",
        title="Perception Demo",
        server_key="perception",
    )

    with gr.Blocks():
        components = window.build(ctx)

    assert components["image_selector"].choices == [("Sample Image", "sample_image")]

def test_preview_perception_request_returns_summarized_request_json() -> None:
    summary = preview_perception_request(
        image_payload={
            "content_type": "image/png",
            "filename": "sample.png",
            "data": "x" * 40,
        },
        iou_threshold=0.5,
        conf_threshold=0.35,
        show_class_id=True,
        show_conf=False,
        request_id="req-perception-preview",
        max_string_length=10,
    )

    assert summary["input"]["image"]["data"] == "<base64 length=40>"
    assert summary["input"]["iou_threshold"] == 0.5
    assert summary["visualization"] == {
        "show_class_id": True,
        "show_conf": False,
    }
    assert summary["request_id"] == "req-perception-preview"

def test_resolve_perception_image_payload_packs_selected_resource(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "perception_demo" / "resources"
    images_dir = resources_dir / "images"
    images_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (images_dir / "sample.png").write_bytes(b"fake-png" * 40)
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    payload = resolve_perception_image_payload(
        ctx=ctx,
        selected_image_id="sample_image",
        uploaded_image_path=None,
    )

    assert payload["content_type"] == "image/png"
    assert payload["filename"] == "sample.png"
    assert payload["data"]

def test_preview_perception_from_inputs_resolves_image_and_returns_request_json(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "perception_demo" / "resources"
    images_dir = resources_dir / "images"
    images_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (images_dir / "sample.png").write_bytes(b"fake-png" * 40)
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    request_json = preview_perception_from_inputs(
        ctx=ctx,
        selected_image_id="sample_image",
        uploaded_image_path=None,
        iou_threshold=0.6,
        conf_threshold=0.4,
        show_class_id=True,
        show_conf=True,
        request_id="req-preview",
    )

    assert request_json["input"]["image"]["data"].startswith("<base64 length=")
    assert request_json["input"]["iou_threshold"] == 0.6
    assert request_json["visualization"] == {"show_class_id": True, "show_conf": True}

class FakePerceptionRenderClient:
    def __init__(self) -> None:
        self.calls = []

    def render_image_response(self, server_key, payload):
        self.calls.append((server_key, payload))
        return "image-result", {
            "status": "success",
            "image": {"content_type": "image/png", "data": "x" * 200},
            "meta": {"elapsed_ms": 9},
        }


class FakePerceptionCtx:
    def __init__(self, project_root):
        self.project_root = project_root
        self.render_client = FakePerceptionRenderClient()

    def component_resource_path(self, component_name, *parts):
        return self.project_root / "components" / component_name / "resources" / Path(*parts)


def test_run_perception_render_from_inputs_calls_render_client_and_returns_outputs(tmp_path) -> None:
    resources_dir = tmp_path / "components" / "perception_demo" / "resources"
    images_dir = resources_dir / "images"
    images_dir.mkdir(parents=True)
    (resources_dir / "manifest.json").write_text(
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
    (images_dir / "sample.png").write_bytes(b"fake-png" * 40)
    ctx = FakePerceptionCtx(tmp_path)

    image, status, request_json, response_json = run_perception_render_from_inputs(
        ctx=ctx,
        server_key="perception",
        selected_image_id="sample_image",
        uploaded_image_path=None,
        iou_threshold=0.6,
        conf_threshold=0.4,
        show_class_id=True,
        show_conf=False,
        request_id="req-render",
    )

    assert image == "image-result"
    assert status == "Success. elapsed_ms=9"
    assert request_json["input"]["image"]["data"].startswith("<base64 length=")
    assert response_json["image"]["data"] == "<base64 length=200>"
    assert ctx.render_client.calls[0][0] == "perception"
    assert ctx.render_client.calls[0][1]["visualization"] == {
        "show_class_id": True,
        "show_conf": False,
    }

