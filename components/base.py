from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class BaseVisWindow(ABC):
    """Base contract for embeddable Gradio visualization windows.

    Attributes:
        window_id: Stable identifier for this visualization window instance.
        title: Human-readable title shown by the containing layout.
        server_key: Key used to resolve the bound algorithm server from config.
    """

    window_id: str
    title: str
    server_key: str

    @abstractmethod
    def build(self, ctx: Any) -> Any:
        """Build this visualization window inside the current Gradio container.

        Args:
            ctx: Application context providing config, clients, and resource helpers.

        Returns:
            Optional framework-specific build result; most Gradio windows return None.
        """
        raise NotImplementedError
