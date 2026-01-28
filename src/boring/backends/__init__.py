"""Backend factory for creating backend client instances."""

from typing import Optional

from .base import BackendClient, TaskItem, BoardInfo, SectionInfo
from .lark import LarkBackend
from .kanban import KanbanBackend
from .. import config


class BackendFactory:
    """Factory for creating backend client instances."""

    @staticmethod
    def create_backend(backend_type: Optional[str] = None) -> BackendClient:
        """Create and return appropriate backend client based on configuration.

        Args:
            backend_type: Override backend type from config. If None, uses config value.

        Returns:
            Configured backend client instance.

        Raises:
            ValueError: If backend type is invalid or not configured.
        """
        backend = backend_type or config.get_backend_type()

        if backend == "lark":
            return LarkBackend(
                server_url=config.get_server_url(),
                jwt_token=config.get_jwt_token(),
                lark_token=config.get_lark_token(),
                tasklist_guid=config.get_tasklist_guid(),
                section_guid=config.get_section_guid(),
                solved_section_guid=config.get_solved_section_guid(),
            )
        elif backend == "kanban":
            return KanbanBackend(
                base_url=config.get_kanban_base_url(),
                api_key=config.get_kanban_api_key(),
                board_id=config.get_kanban_board_id(),
                list_id=config.get_kanban_list_id(),
                done_list_id=config.get_kanban_done_list_id(),
            )
        else:
            raise ValueError(f"Unknown backend type: {backend}")

    @staticmethod
    def get_available_backends() -> list[str]:
        """Return list of available backend types.

        Returns:
            List of backend type identifiers.
        """
        return ["lark", "kanban"]


def get_backend() -> BackendClient:
    """Get the configured backend client.

    Returns:
        Backend client instance based on current configuration.

    Raises:
        ValueError: If backend type is invalid or not configured.
    """
    return BackendFactory.create_backend()


# Export public API
__all__ = [
    "BackendClient",
    "TaskItem",
    "BoardInfo",
    "SectionInfo",
    "BackendFactory",
    "get_backend",
    "LarkBackend",
    "KanbanBackend",
]
