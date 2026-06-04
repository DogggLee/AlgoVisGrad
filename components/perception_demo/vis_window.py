from __future__ import annotations

from pathlib import Path
from typing import Any

import gradio as gr

from components.base import BaseVisWindow
from utils.payload_utils import summarize_large_fields
from utils.resource_utils import load_manifest, pack_resource


def load_perception_examples(ctx: Any) -> list[dict[str, str]]:
    """Load selectable perception image example metadata from resources.

    Args:
        ctx: Application context used to resolve the perception resources path.

    Returns:
        List of dictionaries with `id` and `name` for example selection UI.
    """
    resources_dir = ctx.component_resource_path("perception_demo")
    return [
        {"id": str(item["id"]), "name": str(item["name"])}
        for item in load_manifest(resources_dir)
    ]


def build_perception_payload(
    image_payload: dict[str, Any],
    iou_threshold: float,
    conf_threshold: float,
    show_class_id: bool,
    show_conf: bool,
    request_id: str,
) -> dict[str, Any]:
    """Build the standard render request payload for the perception demo.

    Args:
        image_payload: Packed image payload with content_type, filename, and base64 data.
        iou_threshold: IoU threshold parameter sent to the perception algorithm.
        conf_threshold: Confidence threshold parameter sent to the perception algorithm.
        show_class_id: Whether the returned visualization should draw class IDs.
        show_conf: Whether the returned visualization should draw confidence values.
        request_id: Client-generated request identifier for debugging/reproduction.

    Returns:
        Render request payload using the platform `input`/`visualization` protocol.
    """
    return {
        "input": {
            "image": image_payload,
            "iou_threshold": iou_threshold,
            "conf_threshold": conf_threshold,
        },
        "visualization": {
            "show_class_id": show_class_id,
            "show_conf": show_conf,
        },
        "request_id": request_id,
    }

def resolve_perception_image_payload(
    ctx: Any,
    selected_image_id: str | None,
    uploaded_image_path: str | None,
) -> dict[str, Any]:
    """Resolve the perception image input from upload or selected resource.

    Args:
        ctx: Application context used to resolve perception resources.
        selected_image_id: Optional manifest id selected from the image examples.
        uploaded_image_path: Optional filesystem path from the upload component.

    Returns:
        Packed image payload with content_type, filename, and base64 data.
    """
    if uploaded_image_path:
        image_path = Path(uploaded_image_path)
        suffix = image_path.suffix.lower()
        content_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
        return pack_resource(
            image_path.parent,
            {
                "data": image_path.name,
                "content_type": content_type,
            },
        )

    resources_dir = ctx.component_resource_path("perception_demo")
    manifest = load_manifest(resources_dir)
    item = next(item for item in manifest if item["id"] == selected_image_id)
    return pack_resource(resources_dir, item)


def preview_perception_request(
    image_payload: dict[str, Any],
    iou_threshold: float,
    conf_threshold: float,
    show_class_id: bool,
    show_conf: bool,
    request_id: str,
    max_string_length: int = 120,
) -> dict[str, Any]:
    """Build a summarized perception render request preview.

    Args:
        image_payload: Packed image payload with base64 data.
        iou_threshold: IoU threshold parameter sent to the perception algorithm.
        conf_threshold: Confidence threshold parameter sent to the perception algorithm.
        show_class_id: Whether class IDs should be drawn.
        show_conf: Whether confidence values should be drawn.
        request_id: Client-generated request identifier for debugging/reproduction.
        max_string_length: Strings longer than this are summarized in preview output.

    Returns:
        Summarized render request payload suitable for Request JSON display.
    """
    payload = build_perception_payload(
        image_payload=image_payload,
        iou_threshold=iou_threshold,
        conf_threshold=conf_threshold,
        show_class_id=show_class_id,
        show_conf=show_conf,
        request_id=request_id,
    )
    return summarize_large_fields(payload, max_string_length=max_string_length)


def preview_perception_from_inputs(
    ctx: Any,
    selected_image_id: str | None,
    uploaded_image_path: str | None,
    iou_threshold: float,
    conf_threshold: float,
    show_class_id: bool,
    show_conf: bool,
    request_id: str,
) -> dict[str, Any]:
    """Build perception request preview from UI input values.

    Args:
        ctx: Application context used to resolve image resources.
        selected_image_id: Optional selected image manifest id.
        uploaded_image_path: Optional uploaded image path.
        iou_threshold: IoU threshold parameter.
        conf_threshold: Confidence threshold parameter.
        show_class_id: Whether class IDs should be drawn.
        show_conf: Whether confidence values should be drawn.
        request_id: Client-generated request identifier.

    Returns:
        Summarized render request payload for Request JSON display.
    """
    image_payload = resolve_perception_image_payload(
        ctx=ctx,
        selected_image_id=selected_image_id,
        uploaded_image_path=uploaded_image_path,
    )
    return preview_perception_request(
        image_payload=image_payload,
        iou_threshold=iou_threshold,
        conf_threshold=conf_threshold,
        show_class_id=show_class_id,
        show_conf=show_conf,
        request_id=request_id,
    )


def run_perception_render_from_inputs(
    ctx: Any,
    server_key: str,
    selected_image_id: str | None,
    uploaded_image_path: str | None,
    iou_threshold: float,
    conf_threshold: float,
    show_class_id: bool,
    show_conf: bool,
    request_id: str,
) -> tuple[Any, str, dict[str, Any], dict[str, Any]]:
    """Send a perception render request from UI input values.

    Args:
        ctx: Application context with render client and resource helpers.
        server_key: Config key identifying the bound perception algorithm server.
        selected_image_id: Optional selected image manifest id.
        uploaded_image_path: Optional uploaded image path.
        iou_threshold: IoU threshold parameter.
        conf_threshold: Confidence threshold parameter.
        show_class_id: Whether class IDs should be drawn.
        show_conf: Whether confidence values should be drawn.
        request_id: Client-generated request identifier.

    Returns:
        Tuple of image result, status text, request JSON, and response JSON.
    """
    image_payload = resolve_perception_image_payload(
        ctx=ctx,
        selected_image_id=selected_image_id,
        uploaded_image_path=uploaded_image_path,
    )
    payload = build_perception_payload(
        image_payload=image_payload,
        iou_threshold=iou_threshold,
        conf_threshold=conf_threshold,
        show_class_id=show_class_id,
        show_conf=show_conf,
        request_id=request_id,
    )
    request_json = summarize_large_fields(payload)

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

    response_json = summarize_large_fields(response_payload)
    meta = response_payload.get("meta", {})
    elapsed_ms = meta.get("elapsed_ms")
    status = "Success." if elapsed_ms is None else f"Success. elapsed_ms={elapsed_ms}"
    return image, status, request_json, response_json


class PerceptionDemoVisWindow(BaseVisWindow):
    """Embeddable Gradio visualization window for perception image rendering.

    Attributes:
        window_id: Stable identifier for this window instance.
        title: Human-readable title shown by the containing app layout.
        server_key: Config key for the bound algorithm server.
    """

    def build(self, ctx: Any) -> dict[str, Any]:
        """Build perception demo controls inside the current Gradio container.

        Args:
            ctx: Application context with config, clients, and resource helpers.

        Returns:
            Dictionary of important Gradio components created by this window.
        """
        gr.Markdown(f"## {self.title}")
        try:
            examples = load_perception_examples(ctx)
        except (FileNotFoundError, KeyError):
            examples = []
        example_choices = [(example["name"], example["id"]) for example in examples]

        with gr.Row():
            with gr.Column():
                image_selector = gr.Dropdown(
                    label="Image Example",
                    choices=example_choices,
                    value=None,
                    interactive=True,
                )
                uploaded_image = gr.Image(label="Upload Image", type="filepath")
                iou_threshold = gr.Slider(
                    label="IoU Threshold", minimum=0.0, maximum=1.0, value=0.5, step=0.01
                )
                conf_threshold = gr.Slider(
                    label="Confidence Threshold", minimum=0.0, maximum=1.0, value=0.35, step=0.01
                )
                preview_button = gr.Button("Preview", size="sm")
                render_button = gr.Button("Send", size="sm", variant="primary")
            with gr.Column():
                with gr.Row():
                    show_class_id = gr.Checkbox(label="Show Class ID", value=True)
                    show_conf = gr.Checkbox(label="Show Confidence", value=True)
                output_image = gr.Image(label="Visualization Result")
                status_text = gr.Textbox(label="Status / Error", interactive=False)

        with gr.Tabs():
            with gr.Tab("Request JSON"):
                request_json = gr.JSON(label="Request JSON")
            with gr.Tab("Response JSON"):
                response_json = gr.JSON(label="Response JSON")

        def preview_request(
            selected_image_id: str | None,
            uploaded_image_path: str | None,
            iou_value: float,
            conf_value: float,
            show_class_id_value: bool,
            show_conf_value: bool,
        ) -> dict[str, Any]:
            return preview_perception_from_inputs(
                ctx=ctx,
                selected_image_id=selected_image_id,
                uploaded_image_path=uploaded_image_path,
                iou_threshold=iou_value,
                conf_threshold=conf_value,
                show_class_id=show_class_id_value,
                show_conf=show_conf_value,
                request_id=f"{self.window_id}-preview",
            )

        def send_render(
            selected_image_id: str | None,
            uploaded_image_path: str | None,
            iou_value: float,
            conf_value: float,
            show_class_id_value: bool,
            show_conf_value: bool,
        ) -> tuple[Any, str, dict[str, Any], dict[str, Any]]:
            return run_perception_render_from_inputs(
                ctx=ctx,
                server_key=self.server_key,
                selected_image_id=selected_image_id,
                uploaded_image_path=uploaded_image_path,
                iou_threshold=iou_value,
                conf_threshold=conf_value,
                show_class_id=show_class_id_value,
                show_conf=show_conf_value,
                request_id=f"{self.window_id}-render",
            )

        preview_button.click(
            fn=preview_request,
            inputs=[
                image_selector,
                uploaded_image,
                iou_threshold,
                conf_threshold,
                show_class_id,
                show_conf,
            ],
            outputs=[request_json],
        )
        render_button.click(
            fn=send_render,
            inputs=[
                image_selector,
                uploaded_image,
                iou_threshold,
                conf_threshold,
                show_class_id,
                show_conf,
            ],
            outputs=[output_image, status_text, request_json, response_json],
        )

        return {
            "image_selector": image_selector,
            "uploaded_image": uploaded_image,
            "iou_threshold": iou_threshold,
            "conf_threshold": conf_threshold,
            "show_class_id": show_class_id,
            "show_conf": show_conf,
            "preview_button": preview_button,
            "render_button": render_button,
            "output_image": output_image,
            "status_text": status_text,
            "request_json": request_json,
            "response_json": response_json,
        }

