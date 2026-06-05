from __future__ import annotations

from pathlib import Path

import gradio as gr

from components.json_demo.vis_window import JsonDemoVisWindow
from components.path_planner_demo.vis_window import PathPlannerDemoVisWindow
from components.perception_demo.vis_window import PerceptionDemoVisWindow
from utils.app_context import AppContext, create_app_context


RESPONSIVE_SQUARE_MEDIA_CSS = """
#perception-output-image,
#json-demo-output-image {
  width: 100%;
}

#perception-output-image > div,
#json-demo-output-image > div,
#perception-output-image .image-container,
#json-demo-output-image .image-container {
  width: 100% !important;
  aspect-ratio: 1 / 1;
}

#perception-output-image img,
#json-demo-output-image img,
#perception-output-image canvas,
#json-demo-output-image canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
}
"""


def build_app(ctx: AppContext) -> gr.Blocks:
    """Build the top-level Gradio application.

    Args:
        ctx: Application context containing config, clients, and resource helpers.

    Returns:
        Gradio Blocks application ready to launch.
    """
    with gr.Blocks(title=ctx.config.app.title) as app:
        gr.HTML(f"<style>{RESPONSIVE_SQUARE_MEDIA_CSS}</style>")
        gr.Markdown(f"# {ctx.config.app.title}")
        with gr.Tabs():
            with gr.Tab("Perception Demo"):
                PerceptionDemoVisWindow(
                    window_id="perception_demo",
                    title="Perception Demo",
                    server_key="perception",
                ).build(ctx)
            with gr.Tab("Path Planner Demo"):
                PathPlannerDemoVisWindow(
                    window_id="path_planner_demo",
                    title="Path Planner Demo",
                    server_key="path_planner",
                ).build(ctx)
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
