from __future__ import annotations

from pathlib import Path

import gradio as gr

from components.json_demo.vis_window import JsonDemoVisWindow
from utils.app_context import AppContext, create_app_context


def build_app(ctx: AppContext) -> gr.Blocks:
    """Build the top-level Gradio application.

    Args:
        ctx: Application context containing config, clients, and resource helpers.

    Returns:
        Gradio Blocks application ready to launch.
    """
    with gr.Blocks(title=ctx.config.app.title) as app:
        gr.Markdown(f"# {ctx.config.app.title}")
        with gr.Tabs():
            with gr.Tab("Perception Demo"):
                gr.Markdown("Perception demo placeholder")
            with gr.Tab("Path Planner Demo"):
                gr.Markdown("Path planner demo placeholder")
            with gr.Tab("JSON Demo"):
                JsonDemoVisWindow(
                    window_id="json_demo",
                    title="JSON Demo",
                    server_key="json_demo",
                ).build(ctx)
    return app


def main() -> None:
    """Load runtime config, build the Gradio app, and launch the server.

    Args:
        None.

    Returns:
        None. This function blocks while the Gradio server is running.
    """
    project_root = Path(__file__).resolve().parent
    ctx = create_app_context(project_root / "config.yaml", project_root)
    app = build_app(ctx)
    app.launch(
        server_name=ctx.config.app.host,
        server_port=ctx.config.app.port,
    )


if __name__ == "__main__":
    main()
