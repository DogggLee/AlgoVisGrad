from __future__ import annotations

from pathlib import Path


def test_readme_documents_minimum_json_demo_workflow() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "conda activate algo_vis" in readme
    assert "python -m components.json_demo.mock_server" in readme
    assert "python app.py" in readme
    assert "python -m pytest -q" in readme

def test_readme_documents_vis_window_developer_workflow() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "BaseVisWindow" in readme
    assert "build(ctx)" in readme
    assert "Do not create `gr.Blocks`" in readme
    assert "ctx.render_client" in readme
    assert "ctx.health_client" in readme

def test_readme_documents_protocol_content_types_and_coordinates() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "image/png" in readme
    assert "image/jpeg" in readme
    assert "array/list" in readme
    assert "array/npy" in readme
    assert "[H, W]" in readme
    assert "[x, y]" in readme
    assert "array[y, x]" in readme
    assert '"status": "error"' in readme

