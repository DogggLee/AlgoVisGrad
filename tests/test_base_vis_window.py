from __future__ import annotations

import pytest

from components.base import BaseVisWindow


class DemoWindow(BaseVisWindow):
    def build(self, ctx):
        return {"ctx": ctx, "server_key": self.server_key}


def test_base_vis_window_keeps_identity_and_requires_build_contract() -> None:
    window = DemoWindow(
        window_id="json_demo",
        title="JSON Demo",
        server_key="json_server",
    )

    result = window.build(ctx="test-context")

    assert window.window_id == "json_demo"
    assert window.title == "JSON Demo"
    assert window.server_key == "json_server"
    assert result == {"ctx": "test-context", "server_key": "json_server"}


def test_base_vis_window_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        BaseVisWindow(window_id="base", title="Base", server_key="server")
