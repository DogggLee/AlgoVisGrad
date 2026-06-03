from __future__ import annotations

from pathlib import Path


def test_readme_documents_minimum_json_demo_workflow() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "conda activate algo_vis" in readme
    assert "python -m components.json_demo.mock_server" in readme
    assert "python app.py" in readme
    assert "python -m pytest -q" in readme
