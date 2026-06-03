from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from utils.config_utils import AppConfig, load_config
from utils.health_client import HealthClient
from utils.render_client import RenderClient


@dataclass(frozen=True)
class AppContext:
    """Runtime context shared with embeddable visualization windows.

    Attributes:
        config: Loaded platform configuration.
        project_root: Root directory used to resolve component resources.
        health_client: Client used to check configured algorithm server health.
        render_client: Client used to send render requests to algorithm servers.
    """

    config: AppConfig
    project_root: Path
    health_client: HealthClient | None = None
    render_client: RenderClient | None = None

    def component_resource_path(self, component_name: str, *parts: str) -> Path:
        """Resolve a path inside one component's resources directory.

        Args:
            component_name: Name of the component directory under `components`.
            *parts: Optional path segments inside that component's `resources` directory.

        Returns:
            Absolute or project-root-relative path to the requested component resource.
        """
        return self.project_root / "components" / component_name / "resources" / Path(*parts)


def create_app_context(config_path: str | Path, project_root: str | Path) -> AppContext:
    """Create the platform application context from a config file and project root.

    Args:
        config_path: Filesystem path to the runtime YAML configuration.
        project_root: Root directory used for resolving component resource files.

    Returns:
        AppContext containing loaded config, health client, render client, and
        resource path helpers for visualization windows.
    """
    config = load_config(config_path)
    return AppContext(
        config=config,
        project_root=Path(project_root),
        health_client=HealthClient(config),
        render_client=RenderClient(config),
    )
