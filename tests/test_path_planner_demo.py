from __future__ import annotations

from components.path_planner_demo.vis_window import build_path_planner_payload


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
