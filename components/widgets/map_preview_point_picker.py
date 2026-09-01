from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass
from typing import Any

import gradio as gr
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class MapPreviewSelectionEvent:
    """One raw map preview selection event emitted by the point picker.

    Args:
        mouse_button: Mouse button label, usually `left` or `right`.
        cell_x: Selected grid x coordinate.
        cell_y: Selected grid y coordinate.
        is_obstacle: Whether the selected cell is an obstacle in the map array.
    """

    mouse_button: str
    cell_x: int
    cell_y: int
    is_obstacle: bool


def render_map_preview_point_picker_image(
    map_array: np.ndarray | list[list[int]],
    start: tuple[int, int] | None = None,
    goal: tuple[int, int] | None = None,
    target_size: int = 500,
) -> tuple[Image.Image, int]:
    """Render one map preview image with integer nearest-neighbor upscaling.

    Args:
        map_array: 2D map array where non-zero cells are obstacles.
        start: Optional start point as `(x, y)`.
        goal: Optional goal point as `(x, y)`.
        target_size: Target maximum preview dimension before integer scaling.

    Returns:
        Tuple of rendered PIL image and integer preview scale factor.
    """
    grid = np.asarray(map_array, dtype=np.uint8)
    height = max(int(grid.shape[0]), 1)
    width = max(int(grid.shape[1]), 1)
    base_image = Image.new("RGB", (width, height), color=(255, 255, 255))

    for y in range(height):
        for x in range(width):
            if int(grid[y, x]):
                base_image.putpixel((x, y), (55, 55, 55))

    if start is not None:
        start_x, start_y = int(start[0]), int(start[1])
        if 0 <= start_x < width and 0 <= start_y < height:
            base_image.putpixel((start_x, start_y), (0, 200, 0))
    if goal is not None:
        goal_x, goal_y = int(goal[0]), int(goal[1])
        if 0 <= goal_x < width and 0 <= goal_y < height:
            base_image.putpixel((goal_x, goal_y), (220, 0, 0))

    preview_scale = max(target_size // max(width, height), 1)
    return (
        base_image.resize((width * preview_scale, height * preview_scale), Image.Resampling.NEAREST),
        preview_scale,
    )


def parse_map_preview_selection_event(value: str | None) -> MapPreviewSelectionEvent | None:
    """Parse one JSON-encoded picker event payload into a typed event.

    Args:
        value: JSON string emitted by the point picker event channel.

    Returns:
        Parsed selection event, or None when the value is empty.
    """
    if not value:
        return None

    payload = json.loads(value)
    return MapPreviewSelectionEvent(
        mouse_button=str(payload["mouse_button"]),
        cell_x=int(payload["cell_x"]),
        cell_y=int(payload["cell_y"]),
        is_obstacle=bool(payload["is_obstacle"]),
    )


class MapPreviewPointPicker:
    """Project-local map preview component with click-based point picking.

    Args:
        picker_id: Stable DOM/component id used for the preview surface.
        target_size: Target maximum preview dimension before integer scaling.
    """

    def __init__(self, picker_id: str, target_size: int = 500) -> None:
        self.picker_id = picker_id
        self.target_size = target_size
        self.event_channel_id = f"{picker_id}-event"

    def build(
        self,
        map_array: np.ndarray | list[list[int]] | None,
        start: tuple[int, int] | None = None,
        goal: tuple[int, int] | None = None,
    ) -> dict[str, gr.Component]:
        """Build preview and hidden event-channel components for one picker.

        Args:
            map_array: Initial map array to display.
            start: Optional initial start point.
            goal: Optional initial goal point.

        Returns:
            Dictionary containing the visible preview HTML and hidden event channel.
        """
        preview = gr.HTML(
            value=self.render(map_array=map_array, start=start, goal=goal),
            elem_id=self.picker_id,
        )
        event_channel = gr.Textbox(
            value="",
            show_label=False,
            container=False,
            elem_id=self.event_channel_id,
        )
        return {"preview": preview, "event_channel": event_channel}

    def render(
        self,
        map_array: np.ndarray | list[list[int]] | None,
        start: tuple[int, int] | None = None,
        goal: tuple[int, int] | None = None,
    ) -> str:
        """Render one complete picker HTML block for the current map state.

        Args:
            map_array: Map array to visualize.
            start: Optional current start point.
            goal: Optional current goal point.

        Returns:
            HTML string containing the preview image and localized click handler.
        """
        if map_array is None:
            return (
                f'<style>#{self.event_channel_id}{{display:none !important;}}</style>'
                '<div style="min-height: 120px;"></div>'
            )

        preview_image, preview_scale = render_map_preview_point_picker_image(
            map_array=map_array,
            start=start,
            goal=goal,
            target_size=self.target_size,
        )
        buffer = io.BytesIO()
        preview_image.save(buffer, format="PNG")
        image_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        grid = np.asarray(map_array, dtype=np.uint8)
        map_height = int(grid.shape[0])
        map_width = int(grid.shape[1])
        wrapper_id = f"{self.picker_id}-wrapper"
        image_id = f"{self.picker_id}-image"
        script_id = f"{self.picker_id}-script"

        return f"""
<style>
#{self.event_channel_id} {{
  display: none !important;
}}
#{wrapper_id} {{
  max-width: 100%;
  overflow: auto;
}}
#{image_id} {{
  display: block;
  image-rendering: pixelated;
  user-select: none;
  -webkit-user-drag: none;
}}
</style>
<div id="{wrapper_id}">
  <img
    id="{image_id}"
    src="data:image/png;base64,{image_b64}"
    width="{preview_image.width}"
    height="{preview_image.height}"
    alt="map preview"
    oncontextmenu="return false;"
  />
</div>
<script id="{script_id}">
(() => {{
  const wrapper = document.getElementById("{wrapper_id}");
  const img = document.getElementById("{image_id}");
  if (!wrapper || !img || wrapper.dataset.mapPickerBound === "true") {{
    return;
  }}
  wrapper.dataset.mapPickerBound = "true";
  const previewScale = {preview_scale};
  const mapWidth = {map_width};
  const mapHeight = {map_height};
  const obstacleGrid = {json.dumps(grid.tolist())};
  const eventChannelRoot = document.getElementById("{self.event_channel_id}");
  const eventInput = eventChannelRoot && (eventChannelRoot.querySelector("textarea") || eventChannelRoot.querySelector("input"));
  if (!eventInput) {{
    return;
  }}
  const setNativeInputValue = (inputElement, nextValue) => {{
    const prototype = inputElement.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");
    if (descriptor && descriptor.set) {{
      descriptor.set.call(inputElement, nextValue);
      return;
    }}
    inputElement.value = nextValue;
  }};

  const emitSelection = (mouseButton, event) => {{
    event.preventDefault();
    const rect = img.getBoundingClientRect();
    const renderedWidth = Math.max(rect.width, 1);
    const renderedHeight = Math.max(rect.height, 1);
    const pixelX = Math.max(0, Math.min(img.width - 1, Math.floor((event.clientX - rect.left) * (img.width / renderedWidth))));
    const pixelY = Math.max(0, Math.min(img.height - 1, Math.floor((event.clientY - rect.top) * (img.height / renderedHeight))));
    const cellX = Math.max(0, Math.min(mapWidth - 1, Math.floor(pixelX / previewScale)));
    const cellY = Math.max(0, Math.min(mapHeight - 1, Math.floor(pixelY / previewScale)));
    const payload = JSON.stringify({{
      mouse_button: mouseButton,
      cell_x: cellX,
      cell_y: cellY,
      is_obstacle: Boolean(obstacleGrid[cellY][cellX]),
      emitted_at: Date.now()
    }});
    setNativeInputValue(eventInput, payload);
    eventInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
    eventInput.dispatchEvent(new Event("change", {{ bubbles: true }}));
  }};

  wrapper.addEventListener("mousedown", (event) => {{
    if (event.target !== img) {{
      return;
    }}
    if (event.button === 0) {{
      emitSelection("left", event);
      return;
    }}
    if (event.button === 2) {{
      emitSelection("right", event);
    }}
  }});
  wrapper.addEventListener("contextmenu", (event) => {{
    if (event.target === img) {{
      event.preventDefault();
    }}
  }});
}})();
</script>
"""
