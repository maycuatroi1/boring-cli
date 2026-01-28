"""Base classes and data models for backend implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class TaskItem:
    """Normalized task representation across backends."""

    id: str
    title: str
    description: str
    priority: Optional[str] = None
    due_date: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BoardInfo:
    """Normalized board/tasklist representation."""

    id: str
    name: str


@dataclass
class SectionInfo:
    """Normalized section/column representation."""

    id: str
    name: str
    board_id: str


class BackendClient(ABC):
    """Abstract base class for task management backends."""

    @abstractmethod
    def list_boards(self) -> List[BoardInfo]:
        """List all boards/tasklists available to the user.

        Returns:
            List of BoardInfo objects representing available boards/tasklists.

        Raises:
            Exception: If the API call fails or authentication is invalid.
        """
        pass

    @abstractmethod
    def get_board_info(self, board_id: str) -> Dict[str, Any]:
        """Get board details including sections/columns.

        Args:
            board_id: The unique identifier for the board/tasklist.

        Returns:
            Dictionary containing board details.

        Raises:
            Exception: If the board is not found or API call fails.
        """
        pass

    @abstractmethod
    def list_sections(self, board_id: str) -> List[SectionInfo]:
        """List all sections/columns in a board/tasklist.

        Args:
            board_id: The unique identifier for the board/tasklist.

        Returns:
            List of SectionInfo objects representing sections/columns.

        Raises:
            Exception: If the board is not found or API call fails.
        """
        pass

    @abstractmethod
    def list_tasks(
        self, section_id: str, labels: Optional[List[str]] = None
    ) -> List[TaskItem]:
        """List all tasks/cards in a section with optional label filtering.

        Args:
            section_id: The unique identifier for the section/column.
            labels: Optional list of labels to filter tasks by.

        Returns:
            List of TaskItem objects representing tasks/cards.

        Raises:
            Exception: If the section is not found or API call fails.
        """
        pass

    @abstractmethod
    def get_task_detail(self, task_id: str) -> TaskItem:
        """Get detailed information about a specific task/card.

        Args:
            task_id: The unique identifier for the task/card.

        Returns:
            TaskItem object with full task details including comments.

        Raises:
            Exception: If the task is not found or API call fails.
        """
        pass

    @abstractmethod
    def move_task(
        self, task_id: str, from_section_id: str, to_section_id: str
    ) -> bool:
        """Move a task/card from one section to another.

        Args:
            task_id: The unique identifier for the task/card.
            from_section_id: The source section/column identifier.
            to_section_id: The destination section/column identifier.

        Returns:
            True if the move was successful, False otherwise.

        Raises:
            Exception: If the task or sections are not found, or API call fails.
        """
        pass

    @abstractmethod
    def get_backend_type(self) -> str:
        """Return backend type identifier.

        Returns:
            String identifier for the backend ('lark' or 'kanban').
        """
        pass

    @abstractmethod
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate backend configuration.

        Returns:
            Tuple of (is_valid, error_message). If configuration is valid,
            returns (True, None). Otherwise returns (False, error_message).
        """
        pass
