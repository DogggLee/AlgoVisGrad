from __future__ import annotations

from typing import Any


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
