from __future__ import annotations

import gradio as gr

from components.widgets.map_preview_point_picker import (
    MapPreviewPointPicker,
    parse_map_preview_selection_event,
    render_map_preview_point_picker_image,
)


def test_render_map_preview_point_picker_image_uses_integer_nearest_scaling() -> None:
    image, preview_scale = render_map_preview_point_picker_image(
        map_array=[[0, 1, 0], [0, 0, 0]],
        start=(0, 0),
        goal=(2, 1),
        target_size=500,
    )

    assert preview_scale == 166
    assert image.size == (498, 332)
    assert image.getpixel((0, 0)) == (0, 200, 0)
    assert image.getpixel((image.width - 1, image.height - 1)) == (220, 0, 0)


def test_parse_map_preview_selection_event_returns_typed_event() -> None:
    event = parse_map_preview_selection_event(
        '{"mouse_button":"right","cell_x":12,"cell_y":7,"is_obstacle":true,"emitted_at":1}'
    )

    assert event is not None
    assert event.mouse_button == "right"
    assert event.cell_x == 12
    assert event.cell_y == 7
    assert event.is_obstacle is True


def test_map_preview_point_picker_builds_preview_and_hidden_event_channel() -> None:
    picker = MapPreviewPointPicker(picker_id="demo-picker", target_size=500)

    with gr.Blocks():
        components = picker.build(map_array=[[0, 1], [0, 0]], start=(0, 0), goal=(1, 1))

    assert components["preview"].elem_id == "demo-picker"
    assert components["event_channel"].elem_id == "demo-picker-event"
    assert "contextmenu" in components["preview"].value
    assert 'oncontextmenu="return false;"' in components["preview"].value
    assert "addEventListener(\"mousedown\"" in components["preview"].value
    assert "setNativeInputValue" in components["preview"].value
    assert "mouse_button:" in components["preview"].value
