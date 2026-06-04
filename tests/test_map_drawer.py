from __future__ import annotations

import json

import numpy as np

from map_drawer import (
    add_map_border,
    create_blank_map,
    create_map_canvas,
    erase_map_cell,
    fill_map_cell,
    random_fill_obstacles,
    reset_map_obstacles,
    scale_cell_size,
    save_map_data,
    sketch_to_map,
)


def test_create_blank_map_returns_zero_filled_uint8_grid() -> None:
    grid = create_blank_map(height=4, width=6)

    assert grid.shape == (4, 6)
    assert grid.dtype == np.uint8
    assert np.count_nonzero(grid) == 0


def test_create_map_canvas_scales_map_by_cell_size() -> None:
    canvas = create_map_canvas(height=3, width=5, cell_size=12)

    assert canvas.size == (60, 36)


def test_sketch_to_map_marks_cells_touched_by_dark_strokes_as_obstacles() -> None:
    sketch = np.full((30, 40, 4), 255, dtype=np.uint8)

    sketch[2:8, 3:9] = [0, 0, 0, 255]
    sketch[12:18, 22:28] = [0, 0, 0, 255]

    grid = sketch_to_map(sketch=sketch, height=3, width=4, cell_size=10)

    assert grid.tolist() == [
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 0],
    ]


def test_save_map_data_writes_json_grid(tmp_path) -> None:
    grid = np.array([[0, 1], [1, 0]], dtype=np.uint8)
    output_path = tmp_path / "map.json"

    returned_path = save_map_data(grid=grid, output_path=output_path, output_format="json")

    assert returned_path == output_path
    assert json.loads(output_path.read_text(encoding="utf-8")) == [[0, 1], [1, 0]]


def test_save_map_data_writes_npy_grid(tmp_path) -> None:
    grid = np.array([[0, 1], [1, 0]], dtype=np.uint8)
    output_path = tmp_path / "map.npy"

    returned_path = save_map_data(grid=grid, output_path=output_path, output_format="npy")

    assert returned_path == output_path
    assert np.array_equal(np.load(output_path), grid)


def test_add_map_border_sets_outer_ring_to_obstacles() -> None:
    grid = create_blank_map(height=4, width=5)

    bordered = add_map_border(grid)

    assert bordered.tolist() == [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
    ]


def test_random_fill_obstacles_marks_sampled_cells_using_ratio() -> None:
    grid = create_blank_map(height=4, width=5)

    filled = random_fill_obstacles(grid=grid, obstacle_ratio=0.25, seed=7)

    assert filled.shape == (4, 5)
    assert filled.dtype == np.uint8
    assert np.count_nonzero(filled) == 5


def test_fill_map_cell_sets_one_target_cell_to_obstacle() -> None:
    grid = create_blank_map(height=3, width=4)

    filled = fill_map_cell(grid=grid, row=1, col=2)

    assert filled.tolist() == [
        [0, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 0],
    ]


def test_erase_map_cell_sets_one_target_cell_to_free() -> None:
    grid = np.ones((3, 4), dtype=np.uint8)

    erased = erase_map_cell(grid=grid, row=1, col=2)

    assert erased.tolist() == [
        [1, 1, 1, 1],
        [1, 1, 0, 1],
        [1, 1, 1, 1],
    ]


def test_reset_map_obstacles_clears_all_obstacle_cells() -> None:
    grid = np.array([[1, 0], [1, 1]], dtype=np.uint8)

    cleared = reset_map_obstacles(grid)

    assert cleared.tolist() == [[0, 0], [0, 0]]


def test_scale_cell_size_changes_display_scale_only() -> None:
    grid = np.array([[0, 1], [1, 0]], dtype=np.uint8)

    smaller = scale_cell_size(current_cell_size=20, delta=-1)
    larger = scale_cell_size(current_cell_size=20, delta=1)

    assert smaller == 18
    assert larger == 22
    assert grid.tolist() == [[0, 1], [1, 0]]
