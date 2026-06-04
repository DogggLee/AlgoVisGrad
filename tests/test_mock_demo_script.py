from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_start_mock_demo_script_exists_and_starts_all_three_modules() -> None:
    script_path = Path("start_mock_demo.sh")

    assert script_path.exists()
    assert os.access(script_path, os.X_OK)
    assert "components.perception_demo.mock_server" in script_path.read_text(encoding="utf-8")
    assert "components.path_planner_demo.mock_server" in script_path.read_text(encoding="utf-8")
    assert "components.json_demo.mock_server" in script_path.read_text(encoding="utf-8")


def test_start_mock_demo_script_has_valid_shell_syntax() -> None:
    subprocess.run(["bash", "-n", "start_mock_demo.sh"], check=True)

