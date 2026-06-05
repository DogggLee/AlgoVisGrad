from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import gradio as gr
import numpy as np
from PIL import Image

from components.base import BaseVisWindow
from utils.resource_utils import load_manifest, pack_resource


PATH_PLANNER_DEMO_RESULT_SIZE = 500


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


def resolve_path_planner_map_payload(
    ctx: Any,
    selected_map_id: str | None,
    uploaded_map_path: str | None = None,
) -> dict[str, Any]:
    """Resolve the selected path planner map resource into request payload form.

    Args:
        ctx: Application context used to resolve path planner resources.
        selected_map_id: Manifest id of the selected map example.
        uploaded_map_path: Optional filesystem path to an uploaded JSON or NPY map file.

    Returns:
        Packed map payload with content_type, filename, shape, dtype, and data.
    """
    if uploaded_map_path:
        uploaded_path = Path(uploaded_map_path)
        return _pack_map_payload_from_path(uploaded_path)

    resources_dir = ctx.component_resource_path("path_planner_demo")
    manifest = load_manifest(resources_dir)
    item = next(item for item in manifest if item["id"] == selected_map_id)
    data_path = resources_dir / str(item["data"])
    return _pack_map_payload_from_path(data_path)


def get_path_planner_map_preview(
    ctx: Any,
    selected_map_id: str | None,
    uploaded_map_path: str | None = None,
    start_x: int | None = None,
    start_y: int | None = None,
    goal_x: int | None = None,
    goal_y: int | None = None,
) -> Image.Image | None:
    """Resolve a visual map preview for the selected or uploaded map payload.

    Args:
        ctx: Application context used to resolve path planner resources.
        selected_map_id: Manifest id of the selected map example.
        uploaded_map_path: Optional filesystem path to an uploaded JSON or NPY map file.
        start_x: Optional start point horizontal coordinate for preview overlay.
        start_y: Optional start point vertical coordinate for preview overlay.
        goal_x: Optional goal point horizontal coordinate for preview overlay.
        goal_y: Optional goal point vertical coordinate for preview overlay.

    Returns:
        PIL image preview of the resolved map data, or None when no map is available.
    """
    if uploaded_map_path:
        return _render_map_preview_image(
            _load_map_array_from_path(Path(uploaded_map_path)),
            start_x=start_x,
            start_y=start_y,
            goal_x=goal_x,
            goal_y=goal_y,
        )

    if not selected_map_id:
        return None

    resources_dir = ctx.component_resource_path("path_planner_demo")
    manifest = load_manifest(resources_dir)
    item = next(item for item in manifest if item["id"] == selected_map_id)
    return _render_map_preview_image(
        _load_map_array_from_path(resources_dir / str(item["data"])),
        start_x=start_x,
        start_y=start_y,
        goal_x=goal_x,
        goal_y=goal_y,
    )


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
    shape = item.get("shape")
    if shape:
        height = max(int(shape[0]), 1)
        width = max(int(shape[1]), 1) if len(shape) > 1 else 2
        return width, height
    data = _load_map_array_from_path(resources_dir / str(item["data"]))
    height, width = data.shape[:2]
    return width, height


def get_uploaded_path_planner_map_dimensions(uploaded_map_path: str | None) -> tuple[int, int]:
    """Read uploaded map width and height from a JSON file.

    Args:
        uploaded_map_path: Optional filesystem path to an uploaded JSON or NPY map file.

    Returns:
        Tuple of `(width, height)` for slider range calculation.
    """
    if not uploaded_map_path:
        return 2, 2
    data = _load_map_array_from_path(Path(uploaded_map_path))
    return max(int(data.shape[1]), 1), max(int(data.shape[0]), 1)


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
        max_string_length: Unused compatibility parameter retained for the current public interface.

    Returns:
        Raw render request payload suitable for Request JSON display.
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
    return payload


def preview_path_planner_from_inputs(
    ctx: Any,
    selected_map_id: str | None,
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
    uploaded_map_path: str | None = None,
) -> dict[str, Any]:
    """Build path planner request preview from UI input values.

    Args:
        ctx: Application context used to resolve map resources.
        selected_map_id: Manifest id of the selected map example.
        uploaded_map_path: Optional filesystem path to an uploaded JSON or NPY map file.
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
        Raw render request payload for Request JSON display.
    """
    map_payload = resolve_path_planner_map_payload(
        ctx=ctx,
        selected_map_id=selected_map_id,
        uploaded_map_path=uploaded_map_path,
    )
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
    selected_map_id: str | None,
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
    uploaded_map_path: str | None = None,
) -> tuple[Any, str, dict[str, Any], dict[str, Any]]:
    """Send a path planner render request from UI input values.

    Args:
        ctx: Application context with render client and resource helpers.
        server_key: Config key identifying the bound path planner server.
        selected_map_id: Manifest id of the selected map example.
        uploaded_map_path: Optional filesystem path to an uploaded JSON or NPY map file.
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
    map_payload = resolve_path_planner_map_payload(
        ctx=ctx,
        selected_map_id=selected_map_id,
        uploaded_map_path=uploaded_map_path,
    )
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
    request_json = payload

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

    image = _scale_path_planner_display_image(image)
    response_json = response_payload
    meta = response_payload.get("meta", {})
    elapsed_ms = meta.get("elapsed_ms")
    status = "Success." if elapsed_ms is None else f"Success. elapsed_ms={elapsed_ms}"
    return image, status, request_json, response_json


def format_health_indicator(status_text: str) -> str:
    """Format path planner server status as a Gradio Markdown indicator.

    Args:
        status_text: Human-readable health status text starting with a state name.

    Returns:
        Markdown text with green or red circle status indicator.
    """
    state = status_text.split(":", 1)[0].strip() or "unknown"
    indicator = "🟢" if state == "online" else "🔴"
    return f"{indicator} {state}"


def check_path_planner_demo_health(ctx: Any, server_key: str) -> str:
    """Check the bound path planner server and format status for display.

    Args:
        ctx: Application context containing a health_client.
        server_key: Config key identifying the bound algorithm server.

    Returns:
        Human-readable status text in `state: message` format.
    """
    status = ctx.health_client.check(server_key)
    return f"{status.state}: {status.message}"


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


def build_uploaded_path_planner_slider_updates(
    uploaded_map_path: str | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build slider updates derived from an uploaded map file.

    Args:
        uploaded_map_path: Optional filesystem path to an uploaded JSON or NPY map file.

    Returns:
        Four Gradio update dictionaries for `start_x`, `start_y`, `goal_x`, and `goal_y`.
    """
    width, height = get_uploaded_path_planner_map_dimensions(uploaded_map_path)
    max_x = max(width - 1, 0)
    max_y = max(height - 1, 0)
    return (
        gr.update(maximum=max_x, value=0),
        gr.update(maximum=max_y, value=0),
        gr.update(maximum=max_x, value=max_x),
        gr.update(maximum=max_y, value=max_y),
    )


def _load_map_array_from_path(path: Path) -> np.ndarray:
    """Load one map file into a 2D `uint8` array.

    Args:
        path: Filesystem path to one `.json` or `.npy` map file.

    Returns:
        2D `uint8` map array.
    """
    if path.suffix.lower() == ".npy":
        return np.asarray(np.load(path), dtype=np.uint8)
    return np.asarray(json.loads(path.read_text(encoding="utf-8")), dtype=np.uint8)


def _pack_map_payload_from_path(path: Path) -> dict[str, Any]:
    """Pack one local map file into the standard request payload shape.

    Args:
        path: Filesystem path to one `.json` or `.npy` map file.

    Returns:
        Request payload fragment for `array/list` or `array/npy` content.
    """
    array = _load_map_array_from_path(path)
    if path.suffix.lower() == ".npy":
        return {
            "content_type": "array/npy",
            "filename": path.name,
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "data": base64.b64encode(path.read_bytes()).decode("ascii"),
        }
    return {
        "content_type": "array/list",
        "filename": path.name,
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "data": array.tolist(),
    }


def _render_map_preview_image(
    data: np.ndarray,
    start_x: int | None = None,
    start_y: int | None = None,
    goal_x: int | None = None,
    goal_y: int | None = None,
) -> Image.Image:
    """Render map data into a simple visual preview image.

    Args:
        data: 2D map array where non-zero values are obstacles.
        start_x: Optional start point horizontal coordinate for preview overlay.
        start_y: Optional start point vertical coordinate for preview overlay.
        goal_x: Optional goal point horizontal coordinate for preview overlay.
        goal_y: Optional goal point vertical coordinate for preview overlay.

    Returns:
        PIL preview image scaled by an integer factor so grid cells stay visually crisp.
    """
    height = max(int(data.shape[0]), 1)
    width = max(int(data.shape[1]), 1)
    base_image = Image.new("RGB", (width, height), color=(255, 255, 255))

    for y in range(height):
        for x in range(width):
            if int(data[y, x]):
                base_image.putpixel((x, y), (55, 55, 55))

    if start_x is not None and start_y is not None and 0 <= int(start_x) < width and 0 <= int(start_y) < height:
        base_image.putpixel((int(start_x), int(start_y)), (0, 200, 0))
    if goal_x is not None and goal_y is not None and 0 <= int(goal_x) < width and 0 <= int(goal_y) < height:
        base_image.putpixel((int(goal_x), int(goal_y)), (220, 0, 0))

    preview_target_size = PATH_PLANNER_DEMO_RESULT_SIZE
    scale = max(preview_target_size // max(width, height), 1)
    return base_image.resize((width * scale, height * scale), Image.Resampling.NEAREST)


def _scale_path_planner_display_image(image: Any) -> Any:
    """Scale one path planner image for crisp grid display in the UI.

    Args:
        image: Render result image returned by the render client.

    Returns:
        Original value for non-PIL images, or an integer-upscaled PIL image.
    """
    if not isinstance(image, Image.Image):
        return image

    width = max(int(image.width), 1)
    height = max(int(image.height), 1)
    target_size = PATH_PLANNER_DEMO_RESULT_SIZE
    scale = max(target_size // max(width, height), 1)
    return image.resize((width * scale, height * scale), Image.Resampling.NEAREST)


class PathPlannerDemoVisWindow(BaseVisWindow):
    """Embeddable Gradio visualization window for path planner rendering.
    构建UI界面，以及每个UI控件的响应逻辑

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
        # 先检查指定的算法Server是否正常启动，需要调用该算法Server的/health接口
        try:
            initial_health = check_path_planner_demo_health(ctx, self.server_key)
        except Exception:
            initial_health = "unknown: not checked"

        # 加载示例数据，默认保存在./resources下，由 manifest.json进行管理
        try:
            examples = load_path_planner_examples(ctx)
        except (FileNotFoundError, KeyError):
            examples = []

        initial_map_id = examples[0]["id"] if examples else None
        initial_width, initial_height = get_path_planner_map_dimensions(ctx, initial_map_id)
        initial_max_x = max(initial_width - 1, 0)
        initial_max_y = max(initial_height - 1, 0)
        initial_map_preview = get_path_planner_map_preview(
            ctx,
            initial_map_id,
            start_x=0,
            start_y=0,
            goal_x=initial_max_x,
            goal_y=initial_max_y,
        )

        # Starter template title row: title, service status, and manual refresh.
        # 创建Gradio的UI组件，该部分可以不作任何修改，默认所有算法页面都需要该内容（页面标题，算法Server状态，状态刷新按钮）
        with gr.Row():
            with gr.Column(scale=0, min_width=190):
                title_text = gr.Markdown(f"## {self.title}")
            with gr.Column(scale=0, min_width=90):
                health_indicator = gr.Markdown(format_health_indicator(initial_health))
            with gr.Column(scale=0, min_width=48):
                refresh_health_button = gr.Button("↻", size="sm", min_width=48)

        selected_map_id = gr.State(initial_map_id)

        # Starter template input and render columns: request inputs on the left, render settings and outputs on the right.
        # 核心页面大致分为三块：算法输入列、输出渲染列、和Debug行。 按倒“品”字形排列
        with gr.Row():
            # Starter template input column: built-in examples stay visible, upload is only a supplemental input path.
            # 算法输入列：用于所有算法本身调用所需的输入参数，其对应控件都放在这一列进行排布
            with gr.Column():
                with gr.Row():
                    example_selector = gr.Dropdown(
                        label="Map Example",
                        choices=[(example["name"], example["id"]) for example in examples],
                        value=initial_map_id,
                        interactive=True,
                        scale=5,
                    )
                    uploaded_map = gr.UploadButton(
                        label="Upload Map File",
                        file_types=[".json", ".npy"],
                        type="filepath",
                        size="sm",
                        scale=1,
                        min_width=120,
                    )
                map_preview = gr.Image(
                    label="Selected Map Preview",
                    value=initial_map_preview,
                    interactive=False,
                    elem_id="path-planner-map-preview",
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
                with gr.Row():
                    inflation_radius = gr.Slider(
                        label="Inflation Radius",
                        minimum=0,
                        maximum=20,
                        value=1,
                        step=1,
                        scale=4,
                    )
                    preview_button = gr.Button("Preview", size="sm", scale=1, min_width=96)
                    render_button = gr.Button("Send", size="sm", variant="primary", scale=1, min_width=96)
            # Starter template render column: visualization controls, result canvas, and request outcome.
            # 渲染输出列：用于所有算法渲染所需的参数，以及渲染结果展示
            with gr.Column():
                with gr.Row():
                    show_start = gr.Checkbox(label="Show Start", value=True)
                    show_goal = gr.Checkbox(label="Show Goal", value=True)
                    show_inflation_area = gr.Checkbox(label="Show Inflation", value=False)

                # with gr.Row():
                    show_path_cost = gr.Checkbox(label="Show Path Cost", value=True)
                    show_candidate_paths = gr.Checkbox(label="Show Candidate Paths", value=False)
                    
                output_image = gr.Image(
                    label="Visualization Result",
                    interactive=False,
                    elem_id="path-planner-output-image",
                )
                status_text = gr.Textbox(label="Status / Error", interactive=False)

        # Starter template debug row: request and response payloads stay visible for integration debugging.
        # Debug行：用于展示算法Server的IO原始数据，以便于复现调试
        with gr.Tabs():
            with gr.Tab("Request JSON"):
                request_json = gr.JSON(label="Request JSON")
            with gr.Tab("Response JSON"):
                response_json = gr.JSON(label="Response JSON")

        # Starter template callback definitions: keep map selection, preview, and request workflows readable for copy-and-adapt development.
        # 提前定义每个UI控件的CallBack函数（主要是各类按钮的响应）
        def select_example(selected_map_value: str | None) -> tuple[str | None, Image.Image | None, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
            slider_updates = build_path_planner_slider_updates(ctx, selected_map_value)
            if not selected_map_value:
                return None, None, *slider_updates
            return (
                selected_map_value,
                get_path_planner_map_preview(
                    ctx,
                    selected_map_value,
                    start_x=slider_updates[0]["value"],
                    start_y=slider_updates[1]["value"],
                    goal_x=slider_updates[2]["value"],
                    goal_y=slider_updates[3]["value"],
                ),
                *slider_updates,
            )

        def preview_uploaded_map(uploaded_map_path: str | None) -> tuple[Image.Image | None, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
            slider_updates = build_uploaded_path_planner_slider_updates(uploaded_map_path)
            return (
                get_path_planner_map_preview(
                    ctx,
                    None,
                    uploaded_map_path=uploaded_map_path,
                    start_x=slider_updates[0]["value"],
                    start_y=slider_updates[1]["value"],
                    goal_x=slider_updates[2]["value"],
                    goal_y=slider_updates[3]["value"],
                ),
                *slider_updates,
            )

        def refresh_map_preview(
            selected_map_value: str | None,
            uploaded_map_path: str | None,
            start_x_value: int,
            start_y_value: int,
            goal_x_value: int,
            goal_y_value: int,
        ) -> Image.Image | None:
            return get_path_planner_map_preview(
                ctx,
                selected_map_value,
                uploaded_map_path=uploaded_map_path,
                start_x=start_x_value,
                start_y=start_y_value,
                goal_x=goal_x_value,
                goal_y=goal_y_value,
            )

        def preview_request(
            selected_map_value: str | None,
            uploaded_map_path: str | None,
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
                uploaded_map_path=uploaded_map_path,
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
            selected_map_value: str | None,
            uploaded_map_path: str | None,
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
                uploaded_map_path=uploaded_map_path,
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

        def refresh_health() -> str:
            return format_health_indicator(check_path_planner_demo_health(ctx, self.server_key))

        # Starter template event bindings and returned components: keep the starter flow explicit instead of hiding it behind extra abstraction.
        # 链接UI控件与CallBack函数
        refresh_health_button.click(
            fn=refresh_health,
            inputs=[],
            outputs=[health_indicator],
        )
        example_selector.change(
            fn=select_example,
            inputs=[example_selector],
            outputs=[selected_map_id, map_preview, start_x, start_y, goal_x, goal_y],
        )
        uploaded_map.upload(
            fn=preview_uploaded_map,
            inputs=[uploaded_map],
            outputs=[map_preview, start_x, start_y, goal_x, goal_y],
        )
        start_x.change(
            fn=refresh_map_preview,
            inputs=[selected_map_id, uploaded_map, start_x, start_y, goal_x, goal_y],
            outputs=[map_preview],
        )
        start_y.change(
            fn=refresh_map_preview,
            inputs=[selected_map_id, uploaded_map, start_x, start_y, goal_x, goal_y],
            outputs=[map_preview],
        )
        goal_x.change(
            fn=refresh_map_preview,
            inputs=[selected_map_id, uploaded_map, start_x, start_y, goal_x, goal_y],
            outputs=[map_preview],
        )
        goal_y.change(
            fn=refresh_map_preview,
            inputs=[selected_map_id, uploaded_map, start_x, start_y, goal_x, goal_y],
            outputs=[map_preview],
        )
        preview_button.click(
            fn=preview_request,
            inputs=[
                selected_map_id,
                uploaded_map,
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
                selected_map_id,
                uploaded_map,
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
            "title_text": title_text,
            "health_indicator": health_indicator,
            "refresh_health_button": refresh_health_button,
            "example_selector": example_selector,
            "map_preview": map_preview,
            "selected_map_id": selected_map_id,
            "uploaded_map": uploaded_map,
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
