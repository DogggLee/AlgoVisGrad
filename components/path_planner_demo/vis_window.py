from __future__ import annotations

from typing import Any

import gradio as gr

from components.base import BaseVisWindow
from utils.payload_utils import summarize_large_fields
from utils.resource_utils import load_manifest, pack_resource


def load_path_planner_examples(ctx: Any) -> list[dict[str, str]]:
    """Load selectable path planner map metadata from component resources.

    Args:
        ctx: Application context used to resolve the path planner resources path.

    Returns:
        List of dictionaries with `id` and `name` for map selection UI.
    """
    resources_dir = ctx.component_resource_path("path_planner_demo")
    return [
        {"id": str(item["id"]), "name": str(item["name"])}
        for item in load_manifest(resources_dir)
    ]


def build_path_planner_payload(
    map_payload: dict[str, Any],
    start_x: int,
    start_y: int,
    goal_x: int,
    goal_y: int,
    inflation_radius: int | float,
    show_start: bool,
    show_goal: bool,
    show_path_cost: bool,
    show_candidate_paths: bool,
    show_inflation_area: bool,
    request_id: str,
) -> dict[str, Any]:
    """Build the standard render request payload for the path planner demo.

    Args:
        map_payload: Packed map resource payload using `array/list` or `array/npy`.
        start_x: Start point horizontal coordinate; maps to column index.
        start_y: Start point vertical coordinate; maps to row index.
        goal_x: Goal point horizontal coordinate; maps to column index.
        goal_y: Goal point vertical coordinate; maps to row index.
        inflation_radius: Obstacle inflation radius parameter sent to the algorithm.
        show_start: Whether to draw the start point.
        show_goal: Whether to draw the goal point.
        show_path_cost: Whether to draw path cost information.
        show_candidate_paths: Whether to draw candidate paths.
        show_inflation_area: Whether to draw inflated obstacle area.
        request_id: Client-generated request identifier for debugging/reproduction.

    Returns:
        Render request payload with points encoded as `[x, y]`.
    """
    return {
        "input": {
            "map": map_payload,
            "start": [start_x, start_y],
            "goal": [goal_x, goal_y],
            "inflation_radius": inflation_radius,
        },
        "visualization": {
            "show_start": show_start,
            "show_goal": show_goal,
            "show_path_cost": show_path_cost,
            "show_candidate_paths": show_candidate_paths,
            "show_inflation_area": show_inflation_area,
        },
        "request_id": request_id,
    }


def resolve_path_planner_map_payload(ctx: Any, selected_map_id: str) -> dict[str, Any]:
    """Resolve the selected path planner map resource into request payload form.

    Args:
        ctx: Application context used to resolve path planner resources.
        selected_map_id: Manifest id of the selected map example.

    Returns:
        Packed map payload with content_type, filename, shape, dtype, and data.
    """
    resources_dir = ctx.component_resource_path("path_planner_demo")
    manifest = load_manifest(resources_dir)
    item = next(item for item in manifest if item["id"] == selected_map_id)
    return pack_resource(resources_dir, item)


def get_path_planner_map_dimensions(ctx: Any, selected_map_id: str | None) -> tuple[int, int]:
    """Read the selected map height and width from manifest metadata.

    Args:
        ctx: Application context used to resolve path planner resources.
        selected_map_id: Manifest id of the selected map example.

    Returns:
        Tuple of `(width, height)` for slider range calculation.
    """
    if not selected_map_id:
        return 2, 2

    resources_dir = ctx.component_resource_path("path_planner_demo")
    manifest = load_manifest(resources_dir)
    item = next(item for item in manifest if item["id"] == selected_map_id)
    shape = item.get("shape") or [2, 2]
    height = max(int(shape[0]), 1)
    width = max(int(shape[1]), 1) if len(shape) > 1 else 2
    return width, height


def preview_path_planner_request(
    map_payload: dict[str, Any],
    start_x: int,
    start_y: int,
    goal_x: int,
    goal_y: int,
    inflation_radius: int | float,
    show_start: bool,
    show_goal: bool,
    show_path_cost: bool,
    show_candidate_paths: bool,
    show_inflation_area: bool,
    request_id: str,
    max_string_length: int = 120,
) -> dict[str, Any]:
    """Build a summarized path planner render request preview.

    Args:
        map_payload: Packed map payload.
        start_x: Start point horizontal coordinate.
        start_y: Start point vertical coordinate.
        goal_x: Goal point horizontal coordinate.
        goal_y: Goal point vertical coordinate.
        inflation_radius: Obstacle inflation radius parameter.
        show_start: Whether to draw the start point.
        show_goal: Whether to draw the goal point.
        show_path_cost: Whether to draw path cost information.
        show_candidate_paths: Whether to draw candidate paths.
        show_inflation_area: Whether to draw inflated obstacle area.
        request_id: Client-generated request identifier.
        max_string_length: Strings longer than this are summarized in preview output.

    Returns:
        Summarized render request payload suitable for Request JSON display.
    """
    payload = build_path_planner_payload(
        map_payload=map_payload,
        start_x=start_x,
        start_y=start_y,
        goal_x=goal_x,
        goal_y=goal_y,
        inflation_radius=inflation_radius,
        show_start=show_start,
        show_goal=show_goal,
        show_path_cost=show_path_cost,
        show_candidate_paths=show_candidate_paths,
        show_inflation_area=show_inflation_area,
        request_id=request_id,
    )
    return summarize_large_fields(payload, max_string_length=max_string_length)


def preview_path_planner_from_inputs(
    ctx: Any,
    selected_map_id: str,
    start_x: int,
    start_y: int,
    goal_x: int,
    goal_y: int,
    inflation_radius: int | float,
    show_start: bool,
    show_goal: bool,
    show_path_cost: bool,
    show_candidate_paths: bool,
    show_inflation_area: bool,
    request_id: str,
) -> dict[str, Any]:
    """Build path planner request preview from UI input values.

    Args:
        ctx: Application context used to resolve map resources.
        selected_map_id: Manifest id of the selected map example.
        start_x: Start point horizontal coordinate.
        start_y: Start point vertical coordinate.
        goal_x: Goal point horizontal coordinate.
        goal_y: Goal point vertical coordinate.
        inflation_radius: Obstacle inflation radius parameter.
        show_start: Whether to draw the start point.
        show_goal: Whether to draw the goal point.
        show_path_cost: Whether to draw path cost information.
        show_candidate_paths: Whether to draw candidate paths.
        show_inflation_area: Whether to draw inflated obstacle area.
        request_id: Client-generated request identifier.

    Returns:
        Summarized render request payload for Request JSON display.
    """
    map_payload = resolve_path_planner_map_payload(ctx=ctx, selected_map_id=selected_map_id)
    return preview_path_planner_request(
        map_payload=map_payload,
        start_x=start_x,
        start_y=start_y,
        goal_x=goal_x,
        goal_y=goal_y,
        inflation_radius=inflation_radius,
        show_start=show_start,
        show_goal=show_goal,
        show_path_cost=show_path_cost,
        show_candidate_paths=show_candidate_paths,
        show_inflation_area=show_inflation_area,
        request_id=request_id,
    )


def run_path_planner_render_from_inputs(
    ctx: Any,
    server_key: str,
    selected_map_id: str,
    start_x: int,
    start_y: int,
    goal_x: int,
    goal_y: int,
    inflation_radius: int | float,
    show_start: bool,
    show_goal: bool,
    show_path_cost: bool,
    show_candidate_paths: bool,
    show_inflation_area: bool,
    request_id: str,
) -> tuple[Any, str, dict[str, Any], dict[str, Any]]:
    """Send a path planner render request from UI input values.

    Args:
        ctx: Application context with render client and resource helpers.
        server_key: Config key identifying the bound path planner server.
        selected_map_id: Manifest id of the selected map example.
        start_x: Start point horizontal coordinate.
        start_y: Start point vertical coordinate.
        goal_x: Goal point horizontal coordinate.
        goal_y: Goal point vertical coordinate.
        inflation_radius: Obstacle inflation radius parameter.
        show_start: Whether to draw the start point.
        show_goal: Whether to draw the goal point.
        show_path_cost: Whether to draw path cost information.
        show_candidate_paths: Whether to draw candidate paths.
        show_inflation_area: Whether to draw inflated obstacle area.
        request_id: Client-generated request identifier.

    Returns:
        Tuple of image result, status text, request JSON, and response JSON.
    """
    map_payload = resolve_path_planner_map_payload(ctx=ctx, selected_map_id=selected_map_id)
    payload = build_path_planner_payload(
        map_payload=map_payload,
        start_x=start_x,
        start_y=start_y,
        goal_x=goal_x,
        goal_y=goal_y,
        inflation_radius=inflation_radius,
        show_start=show_start,
        show_goal=show_goal,
        show_path_cost=show_path_cost,
        show_candidate_paths=show_candidate_paths,
        show_inflation_area=show_inflation_area,
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


def build_path_planner_slider_updates(
    ctx: Any,
    selected_map_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build slider updates derived from the selected map shape.

    Args:
        ctx: Application context used to resolve path planner resources.
        selected_map_id: Manifest id of the selected map example.

    Returns:
        Four Gradio update dictionaries for `start_x`, `start_y`, `goal_x`, and `goal_y`.
    """
    width, height = get_path_planner_map_dimensions(ctx=ctx, selected_map_id=selected_map_id)
    max_x = max(width - 1, 0)
    max_y = max(height - 1, 0)

    # Keep start at the origin and move goal to the lower-right corner of the map.
    return (
        gr.update(maximum=max_x, value=0),
        gr.update(maximum=max_y, value=0),
        gr.update(maximum=max_x, value=max_x),
        gr.update(maximum=max_y, value=max_y),
    )


class PathPlannerDemoVisWindow(BaseVisWindow):
    """Embeddable Gradio visualization window for path planner rendering.

    Attributes:
        window_id: Stable identifier for this window instance.
        title: Human-readable title shown by the containing app layout.
        server_key: Config key for the bound algorithm server.
    """

    def build(self, ctx: Any) -> dict[str, Any]:
        """Build path planner demo controls inside the current Gradio container.

        Args:
            ctx: Application context with config, clients, and resource helpers.

        Returns:
            Dictionary of important Gradio components created by this window.
        """
        gr.Markdown(f"## {self.title}")
        try:
            examples = load_path_planner_examples(ctx)
        except (FileNotFoundError, KeyError):
            examples = []

        example_choices = [(example["name"], example["id"]) for example in examples]
        initial_map_id = examples[0]["id"] if examples else None
        initial_width, initial_height = get_path_planner_map_dimensions(ctx, initial_map_id)
        initial_max_x = max(initial_width - 1, 0)
        initial_max_y = max(initial_height - 1, 0)

        with gr.Row():
            with gr.Column():
                map_selector = gr.Dropdown(
                    label="Map Example",
                    choices=example_choices,
                    value=initial_map_id,
                    interactive=True,
                )
                with gr.Row():
                    start_x = gr.Slider(label="Start X", minimum=0, maximum=initial_max_x, value=0, step=1)
                    start_y = gr.Slider(label="Start Y", minimum=0, maximum=initial_max_y, value=0, step=1)
                with gr.Row():
                    goal_x = gr.Slider(
                        label="Goal X",
                        minimum=0,
                        maximum=initial_max_x,
                        value=initial_max_x,
                        step=1,
                    )
                    goal_y = gr.Slider(
                        label="Goal Y",
                        minimum=0,
                        maximum=initial_max_y,
                        value=initial_max_y,
                        step=1,
                    )
                inflation_radius = gr.Slider(
                    label="Inflation Radius",
                    minimum=0,
                    maximum=20,
                    value=1,
                    step=1,
                )
                preview_button = gr.Button("Preview", size="sm")
                render_button = gr.Button("Send", size="sm", variant="primary")
            with gr.Column():
                with gr.Row():
                    show_start = gr.Checkbox(label="Show Start", value=True)
                    show_goal = gr.Checkbox(label="Show Goal", value=True)
                with gr.Row():
                    show_path_cost = gr.Checkbox(label="Show Path Cost", value=True)
                    show_candidate_paths = gr.Checkbox(label="Show Candidate Paths", value=False)
                with gr.Row():
                    show_inflation_area = gr.Checkbox(label="Show Inflation Area", value=False)
                output_image = gr.Image(label="Visualization Result")
                status_text = gr.Textbox(label="Status / Error", interactive=False)

        with gr.Tabs():
            with gr.Tab("Request JSON"):
                request_json = gr.JSON(label="Request JSON")
            with gr.Tab("Response JSON"):
                response_json = gr.JSON(label="Response JSON")

        def preview_request(
            selected_map_value: str,
            start_x_value: int,
            start_y_value: int,
            goal_x_value: int,
            goal_y_value: int,
            inflation_radius_value: int | float,
            show_start_value: bool,
            show_goal_value: bool,
            show_path_cost_value: bool,
            show_candidate_paths_value: bool,
            show_inflation_area_value: bool,
        ) -> dict[str, Any]:
            return preview_path_planner_from_inputs(
                ctx=ctx,
                selected_map_id=selected_map_value,
                start_x=start_x_value,
                start_y=start_y_value,
                goal_x=goal_x_value,
                goal_y=goal_y_value,
                inflation_radius=inflation_radius_value,
                show_start=show_start_value,
                show_goal=show_goal_value,
                show_path_cost=show_path_cost_value,
                show_candidate_paths=show_candidate_paths_value,
                show_inflation_area=show_inflation_area_value,
                request_id=f"{self.window_id}-preview",
            )

        def send_render(
            selected_map_value: str,
            start_x_value: int,
            start_y_value: int,
            goal_x_value: int,
            goal_y_value: int,
            inflation_radius_value: int | float,
            show_start_value: bool,
            show_goal_value: bool,
            show_path_cost_value: bool,
            show_candidate_paths_value: bool,
            show_inflation_area_value: bool,
        ) -> tuple[Any, str, dict[str, Any], dict[str, Any]]:
            return run_path_planner_render_from_inputs(
                ctx=ctx,
                server_key=self.server_key,
                selected_map_id=selected_map_value,
                start_x=start_x_value,
                start_y=start_y_value,
                goal_x=goal_x_value,
                goal_y=goal_y_value,
                inflation_radius=inflation_radius_value,
                show_start=show_start_value,
                show_goal=show_goal_value,
                show_path_cost=show_path_cost_value,
                show_candidate_paths=show_candidate_paths_value,
                show_inflation_area=show_inflation_area_value,
                request_id=f"{self.window_id}-render",
            )

        map_selector.change(
            fn=lambda selected_map_value: build_path_planner_slider_updates(ctx, selected_map_value),
            inputs=[map_selector],
            outputs=[start_x, start_y, goal_x, goal_y],
        )
        preview_button.click(
            fn=preview_request,
            inputs=[
                map_selector,
                start_x,
                start_y,
                goal_x,
                goal_y,
                inflation_radius,
                show_start,
                show_goal,
                show_path_cost,
                show_candidate_paths,
                show_inflation_area,
            ],
            outputs=[request_json],
        )
        render_button.click(
            fn=send_render,
            inputs=[
                map_selector,
                start_x,
                start_y,
                goal_x,
                goal_y,
                inflation_radius,
                show_start,
                show_goal,
                show_path_cost,
                show_candidate_paths,
                show_inflation_area,
            ],
            outputs=[output_image, status_text, request_json, response_json],
        )

        return {
            "map_selector": map_selector,
            "start_x": start_x,
            "start_y": start_y,
            "goal_x": goal_x,
            "goal_y": goal_y,
            "inflation_radius": inflation_radius,
            "show_start": show_start,
            "show_goal": show_goal,
            "show_path_cost": show_path_cost,
            "show_candidate_paths": show_candidate_paths,
            "show_inflation_area": show_inflation_area,
            "preview_button": preview_button,
            "render_button": render_button,
            "output_image": output_image,
            "status_text": status_text,
            "request_json": request_json,
            "response_json": response_json,
        }
