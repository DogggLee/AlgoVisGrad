from pathlib import Path

from utils.config_utils import load_config


def test_load_config_reads_app_and_server_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
app:
  host: 0.0.0.0
  port: 7860
  title: Algorithm Visualization Platform

servers:
  path_planner:
    base_url: http://127.0.0.1:5002
    health_path: /health
    render_path: /render
    timeout_seconds: 30
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.app.host == "0.0.0.0"
    assert config.app.port == 7860
    assert config.app.title == "Algorithm Visualization Platform"
    assert config.servers["path_planner"].base_url == "http://127.0.0.1:5002"
    assert config.servers["path_planner"].health_path == "/health"
    assert config.servers["path_planner"].render_path == "/render"
    assert config.servers["path_planner"].timeout_seconds == 30
