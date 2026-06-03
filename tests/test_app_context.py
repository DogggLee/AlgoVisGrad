from __future__ import annotations

from utils.app_context import AppContext, create_app_context
from utils.config_utils import AppConfig, AppSettings


def test_app_context_resolves_component_resource_paths(tmp_path) -> None:
    ctx = AppContext(
        config=AppConfig(
            app=AppSettings(host="127.0.0.1", port=7860, title="Test"),
            servers={},
        ),
        project_root=tmp_path,
    )

    resource_path = ctx.component_resource_path("path_planner_demo", "maps")

    assert resource_path == tmp_path / "components" / "path_planner_demo" / "resources" / "maps"

def test_create_app_context_loads_config_and_clients(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
app:
  host: 0.0.0.0
  port: 7860
  title: Algorithm Visualization Platform

servers:
  perception:
    base_url: http://127.0.0.1:5001
    health_path: /health
    render_path: /render
    timeout_seconds: 30
""",
        encoding="utf-8",
    )

    ctx = create_app_context(config_path=config_path, project_root=tmp_path)

    assert ctx.config.app.port == 7860
    assert ctx.health_client is not None
    assert ctx.render_client is not None
    assert ctx.component_resource_path("perception_demo") == (
        tmp_path / "components" / "perception_demo" / "resources"
    )

