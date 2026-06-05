from __future__ import annotations

import json
from typing import Any

import gradio as gr

from components.base import BaseVisWindow
from utils.payload_utils import summarize_large_fields
from utils.resource_utils import load_manifest


JSON_DEMO_EDITOR_LINES = 24
JSON_DEMO_RESULT_HEIGHT = 620


def load_json_demo_examples(ctx: Any) -> list[dict[str, str]]:
    """Load selectable JSON demo example metadata from component resources.

    Args:
        ctx: Application context used to resolve the JSON demo resources path.

    Returns:
        List of dictionaries with `id` and `name` for example selection UI.
    """
    resources_dir = ctx.component_resource_path("json_demo")
    return [
        {"id": str(item["id"]), "name": str(item["name"])}
        for item in load_manifest(resources_dir)
    ]


def load_json_demo_example(
    ctx: Any,
    index: int = 0,
    example_id: str | None = None,
) -> dict[str, Any]:
    """Load one JSON demo input example from component resources.

    Args:
        ctx: Application context used to resolve the JSON demo resources path.
        index: Zero-based manifest item index to load when `example_id` is not given.
        example_id: Optional manifest item id to load.

    Returns:
        JSON object containing demo input fields such as group1, group2, and map_size.
    """
    resources_dir = ctx.component_resource_path("json_demo")
    manifest = load_manifest(resources_dir)
    if example_id is None:
        item = manifest[index]
    else:
        item = next(item for item in manifest if item["id"] == example_id)
    data_path = resources_dir / str(item["data"])
    return json.loads(data_path.read_text(encoding="utf-8"))


def parse_json_demo_input(value: str | dict[str, Any] | None) -> dict[str, Any]:
    """Parse the editable JSON demo input value into a request payload object.

    Args:
        value: JSON text from the editable code input, an already parsed dict, or None.

    Returns:
        Parsed JSON object used as the JSON demo `input.payload`.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    stripped = value.strip()
    if not stripped:
        return {}
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("JSON demo input must be a JSON object")
    return parsed


def build_json_demo_payload(
    user_payload: str | dict[str, Any],
    show_cost: bool,
    request_id: str,
) -> dict[str, Any]:
    """Build the standard render request payload for the JSON demo window.

    Args:
        user_payload: User-provided JSON text or object passed under `input.payload`.
        show_cost: Whether the algorithm server should draw cost information.
        request_id: Client-generated request identifier for debugging/reproduction.

    Returns:
        Render request payload using the platform `input`/`visualization` protocol.
    """
    return {
        "input": {
            "payload": user_payload,
        },
        "visualization": {
            "show_cost": show_cost,
        },
        "request_id": request_id,
    }

def preview_json_demo_request(
    user_payload: str | dict[str, Any],
    show_cost: bool,
    request_id: str,
    max_string_length: int = 120,
) -> tuple[dict[str, Any], str]:
    """Build JSON demo preview outputs without sending a render request.

    Args:
        user_payload: User-provided JSON text or object passed under `input.payload`.
        show_cost: Whether cost visualization is requested.
        request_id: Client-generated request identifier for debugging/reproduction.
        max_string_length: Strings longer than this are summarized in the preview.

    Returns:
        Tuple of summarized payload dictionary and complete pretty-printed JSON text.
    """
    try:
        parsed_payload = parse_json_demo_input(user_payload)
    except (json.JSONDecodeError, ValueError):
        error_payload = {
            "status": "error",
            "error": {"message": "invalid JSON input"},
            "request_id": request_id,
        }
        return error_payload, json.dumps(error_payload, ensure_ascii=False, indent=2)

    payload = build_json_demo_payload(
        user_payload=parsed_payload,
        show_cost=show_cost,
        request_id=request_id,
    )
    return (
        summarize_large_fields(payload, max_string_length=max_string_length),
        json.dumps(payload, ensure_ascii=False, indent=2),
    )


def format_json_demo_health_indicator(status_text: str) -> str:
    """Format JSON demo server status as a Gradio Markdown indicator.

    Args:
        status_text: Human-readable health status text starting with a state name.

    Returns:
        Markdown text with green or red circle status indicator.
    """
    state = status_text.split(":", 1)[0].strip() or "unknown"
    indicator = "🟢" if state == "online" else "🔴"
    return f"{indicator} {state}"


def check_json_demo_health(ctx: Any, server_key: str) -> str:
    """Check the bound JSON demo server and format status for display.

    Args:
        ctx: Application context containing a health_client.
        server_key: Config key identifying the bound algorithm server.

    Returns:
        Human-readable status text in `state: message` format.
    """
    status = ctx.health_client.check(server_key)
    return f"{status.state}: {status.message}"


def run_json_demo_render(
    ctx: Any,
    server_key: str,
    user_payload: dict[str, Any],
    show_cost: bool,
    request_id: str,
    max_string_length: int = 120,
) -> tuple[Any, str, dict[str, Any], dict[str, Any]]:
    """Send a JSON demo render request and prepare Gradio UI outputs.

    Args:
        ctx: Application context containing a render_client.
        server_key: Config key identifying the bound algorithm server.
        user_payload: User-provided JSON object passed under `input.payload`.
        show_cost: Whether cost visualization is requested.
        request_id: Client-generated request identifier for debugging/reproduction.
        max_string_length: Strings longer than this are summarized in the preview.

    Returns:
        Tuple of image result, status text, request JSON, and response JSON.
    """
    try:
        parsed_payload = parse_json_demo_input(user_payload)
    except (json.JSONDecodeError, ValueError):
        error_message = "invalid JSON input"
        return (
            None,
            f"Error: {error_message}",
            {"status": "error", "error": {"message": error_message}, "request_id": request_id},
            {"status": "error", "error": {"message": error_message}},
        )

    request_json, _full_text = preview_json_demo_request(
        user_payload=parsed_payload,
        show_cost=show_cost,
        request_id=request_id,
        max_string_length=max_string_length,
    )
    payload = build_json_demo_payload(
        user_payload=parsed_payload,
        show_cost=show_cost,
        request_id=request_id,
    )
    try:
        image, response_payload = ctx.render_client.render_image_response(server_key, payload)
    except Exception as exc:
        error_message = str(exc)
        return (
            None,
            f"Error: {error_message}",
            request_json,
            {"status": "error", "error": {"message": error_message}},
        )

    response_json = summarize_large_fields(response_payload, max_string_length=max_string_length)
    meta = response_payload.get("meta", {})
    elapsed_ms = meta.get("elapsed_ms")
    status = "Success." if elapsed_ms is None else f"Success. elapsed_ms={elapsed_ms}"
    return image, status, request_json, response_json


class JsonDemoVisWindow(BaseVisWindow):
    """Embeddable Gradio visualization window for JSON-driven image rendering.

    Attributes:
        window_id: Stable identifier for this window instance.
        title: Human-readable title shown by the containing app layout.
        server_key: Config key for the bound algorithm server.
    """

    def build(self, ctx: Any) -> dict[str, Any]:
        """Build JSON demo controls inside the current Gradio container.

        Args:
            ctx: Application context with config, clients, and resource helpers.

        Returns:
            Dictionary of important Gradio components created by this window.
        """
        try:
            initial_health = check_json_demo_health(ctx, self.server_key)
        except Exception:
            initial_health = "unknown: not checked"

        # Starter template title row: title, service status, and manual refresh.
        with gr.Row():
            with gr.Column(scale=0, min_width=150):
                title_text = gr.Markdown(f"## {self.title}")
            with gr.Column(scale=0, min_width=90):
                health_indicator = gr.Markdown(format_json_demo_health_indicator(initial_health))
            with gr.Column(scale=0, min_width=48):
                refresh_health_button = gr.Button("↻", size="sm", min_width=48)
        try:
            examples = load_json_demo_examples(ctx)
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            examples = []
        example_choices = [(example["name"], example["id"]) for example in examples]

        # Starter template input and render columns: request inputs on the left, render settings and outputs on the right.
        with gr.Row():
            # Starter template input column: the JSON editor is both the editable workspace and the visible example preview.
            with gr.Column():
                with gr.Row():
                    example_selector = gr.Dropdown(
                        label="JSON Example",
                        choices=example_choices,
                        value=None,
                        interactive=True,
                        scale=4,
                    )
                    preview_button = gr.Button("Preview", size="sm", scale=1, min_width=96)
                    render_button = gr.Button("Send", size="sm", variant="primary", scale=1, min_width=96)
                json_input = gr.Code(
                    label="Input JSON",
                    value="{}",
                    language="json",
                    lines=JSON_DEMO_EDITOR_LINES,
                    interactive=True,
                )
            # Starter template render column: visualization controls, result canvas, and request outcome.
            with gr.Column():
                with gr.Row():
                    show_cost = gr.Checkbox(label="Show Cost", value=True, scale=1)
                output_image = gr.Image(
                    label="Visualization Result",
                    elem_id="json-demo-output-image",
                )
                status_text = gr.Textbox(label="Status / Error", interactive=False)

        # Starter template debug row: request and response payloads stay visible for integration debugging.
        with gr.Tabs():
            with gr.Tab("Request JSON"):
                request_json = gr.JSON(label="Request JSON")
            with gr.Tab("Response JSON"):
                response_json = gr.JSON(label="Response JSON")

        # Starter template callback definitions: keep the example-loading and request workflows explicit for copy-and-adapt development.
        def load_selected_example(example_id: str | None) -> str:
            if not example_id:
                return "{}"
            return json.dumps(load_json_demo_example(ctx, example_id=example_id), ensure_ascii=False, indent=2)

        def preview_request(user_payload: str | dict[str, Any], show_cost_value: bool) -> dict[str, Any]:
            request_payload, _full_text = preview_json_demo_request(
                user_payload=user_payload or {},
                show_cost=show_cost_value,
                request_id=f"{self.window_id}-preview",
            )
            return request_payload

        def send_render(user_payload: str | dict[str, Any], show_cost_value: bool) -> tuple[Any, str, dict[str, Any], dict[str, Any]]:
            return run_json_demo_render(
                ctx=ctx,
                server_key=self.server_key,
                user_payload=user_payload or {},
                show_cost=show_cost_value,
                request_id=f"{self.window_id}-render",
            )

        def refresh_health() -> str:
            return format_json_demo_health_indicator(check_json_demo_health(ctx, self.server_key))

        # Starter template event bindings and returned components: make the starter flow readable without adding extra abstraction layers.
        refresh_health_button.click(
            fn=refresh_health,
            inputs=[],
            outputs=[health_indicator],
        )
        example_selector.change(
            fn=load_selected_example,
            inputs=[example_selector],
            outputs=[json_input],
        )
        preview_button.click(
            fn=preview_request,
            inputs=[json_input, show_cost],
            outputs=[request_json],
        )
        render_button.click(
            fn=send_render,
            inputs=[json_input, show_cost],
            outputs=[output_image, status_text, request_json, response_json],
        )

        return {
            "title_text": title_text,
            "example_selector": example_selector,
            "json_input": json_input,
            "show_cost": show_cost,
            "health_indicator": health_indicator,
            "refresh_health_button": refresh_health_button,
            "preview_button": preview_button,
            "render_button": render_button,
            "output_image": output_image,
            "status_text": status_text,
            "request_json": request_json,
            "response_json": response_json,
        }
