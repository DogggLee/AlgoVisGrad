from __future__ import annotations

from pathlib import Path


def test_gitignore_ignores_generated_python_and_local_artifacts() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "__pycache__/" in gitignore
    assert ".pytest_cache/" in gitignore
    assert "*.py[cod]" in gitignore
    assert ".env" in gitignore
    assert "outputs/" in gitignore
