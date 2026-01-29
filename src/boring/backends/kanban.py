"""Kanban (Outline) backend implementation."""

from typing import Optional, List, Dict, Any

import httpx

from .base import BackendClient, TaskItem, BoardInfo, SectionInfo


class KanbanBackend(BackendClient):
    """Backend implementation for Outline Kanban board."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        board_id: Optional[str] = None,
        list_id: Optional[str] = None,
        done_list_id: Optional[str] = None,
    ):
        """Initialize Kanban backend.

        Args:
            base_url: Base URL of the Kanban service (e.g., https://local.outline.dev:3000).
            api_key: Bearer token for authentication.
            board_id: Default board ID.
            list_id: Default list/column ID for in-progress tasks.
            done_list_id: List/column ID for done/solved tasks.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.board_id = board_id
        self.list_id = list_id
        self.done_list_id = done_list_id

    def _headers(self) -> dict:
        """Get HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request to Kanban API.

        Args:
            endpoint: API endpoint path.
            data: Optional JSON payload.

        Returns:
            JSON response as dictionary.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        if not self.base_url:
            raise Exception("Kanban base URL not configured. Run 'boring setup' first.")
        if not self.api_key:
            raise Exception("Kanban API key not configured. Run 'boring setup' first.")

        with httpx.Client(verify=False) as client:  # verify=False for local dev
            response = client.post(
                f"{self.base_url}{endpoint}",
                headers=self._headers(),
                json=data or {},
            )
            response.raise_for_status()
            return response.json()

    def _map_priority(self, kanban_priority: Optional[int]) -> Optional[str]:
        """Map Kanban numeric priority to standard priority string.

        Args:
            kanban_priority: Numeric priority from Kanban (0-4).

        Returns:
            String priority (None/Low/Medium/High/Urgent).
        """
        if kanban_priority is None:
            return None
        priority_map = {0: "None", 1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
        return priority_map.get(kanban_priority, "None")

    def list_boards(self) -> List[BoardInfo]:
        """List all Kanban boards."""
        data = self._post("/api/kanban.boards.list")

        boards = []
        for board in data.get("boards", []):
            boards.append(BoardInfo(id=board["id"], name=board["name"]))

        return boards

    def get_board_info(self, board_id: str) -> Dict[str, Any]:
        """Get Kanban board details including columns."""
        return self._post("/api/kanban.boards.info", {"id": board_id})

    def list_sections(self, board_id: str) -> List[SectionInfo]:
        """List all columns in a Kanban board."""
        board_info = self.get_board_info(board_id)

        sections = []
        for col in board_info.get("lists", []):
            sections.append(
                SectionInfo(id=col["id"], name=col["name"], board_id=board_id)
            )

        return sections

    def list_tasks(
        self, section_id: str, labels: Optional[List[str]] = None
    ) -> List[TaskItem]:
        """List all cards in a Kanban column."""
        if not self.board_id:
            raise Exception("Kanban board ID not configured. Run 'boring setup' first.")

        # Get board info to find all cards
        board_info = self.get_board_info(self.board_id)

        task_items = []
        label_filter = set(lbl.lower() for lbl in labels) if labels else None

        for card in board_info.get("cards", []):
            # Filter by list/column ID
            if card.get("listId") != section_id:
                continue

            # Get card details
            try:
                card_detail = self._post("/api/kanban.cards.info", {"id": card["id"]})
            except Exception:
                continue

            # Filter by labels if specified
            card_labels = [tag for tag in card_detail.get("tags", [])]
            if label_filter and not any(
                lbl.lower() in label_filter for lbl in card_labels
            ):
                continue

            # Get comments
            try:
                comments_data = self._post(
                    "/api/kanban.cards.comments.list", {"cardId": card["id"]}
                )
                comments = [
                    {"content": comment["text"], "created_at": comment.get("createdAt", "")}
                    for comment in comments_data.get("comments", [])
                ]
            except Exception:
                comments = []

            # Build markdown description
            title = card_detail.get("title", "")
            description = card_detail.get("description", "")
            priority_str = self._map_priority(card_detail.get("priority"))
            due_date = card_detail.get("dueDate")

            full_markdown = f"# {title}\n\n"

            if priority_str:
                full_markdown += f"**Priority:** {priority_str}\n\n"

            if due_date:
                full_markdown += f"**Due:** {due_date}\n\n"

            if card_labels:
                full_markdown += f"**Labels:** {', '.join(card_labels)}\n\n"

            if description:
                full_markdown += "---\n\n"
                full_markdown += description

            if comments:
                full_markdown += "\n\n---\n\n## Comments\n\n"
                for comment in comments:
                    created_at = comment.get("created_at", "")
                    if created_at:
                        full_markdown += f"### {created_at}\n\n"
                    full_markdown += f"{comment['content']}\n\n"

            task_items.append(
                TaskItem(
                    id=card["id"],
                    title=title,
                    description=full_markdown,
                    priority=priority_str,
                    due_date=due_date,
                    labels=card_labels,
                    comments=comments,
                )
            )

        return task_items

    def get_task_detail(self, task_id: str) -> TaskItem:
        """Get detailed Kanban card information."""
        # Get card details
        card_detail = self._post("/api/kanban.cards.info", {"id": task_id})

        # Get comments
        try:
            comments_data = self._post(
                "/api/kanban.cards.comments.list", {"cardId": task_id}
            )
            comments = [
                {"content": comment["text"], "created_at": comment.get("createdAt", "")}
                for comment in comments_data.get("comments", [])
            ]
        except Exception:
            comments = []

        # Build markdown description
        title = card_detail.get("title", "")
        description = card_detail.get("description", "")
        priority_str = self._map_priority(card_detail.get("priority"))
        due_date = card_detail.get("dueDate")
        card_labels = card_detail.get("tags", [])

        full_markdown = f"# {title}\n\n"

        if priority_str:
            full_markdown += f"**Priority:** {priority_str}\n\n"

        if due_date:
            full_markdown += f"**Due:** {due_date}\n\n"

        if card_labels:
            full_markdown += f"**Labels:** {', '.join(card_labels)}\n\n"

        if description:
            full_markdown += "---\n\n"
            full_markdown += description

        if comments:
            full_markdown += "\n\n---\n\n## Comments\n\n"
            for comment in comments:
                created_at = comment.get("created_at", "")
                if created_at:
                    full_markdown += f"### {created_at}\n\n"
                full_markdown += f"{comment['content']}\n\n"

        return TaskItem(
            id=task_id,
            title=title,
            description=full_markdown,
            priority=priority_str,
            due_date=due_date,
            labels=card_labels,
            comments=comments,
        )

    def move_task(
        self, task_id: str, from_section_id: str, to_section_id: str
    ) -> bool:
        """Move a Kanban card to a different column."""
        try:
            self._post(
                "/api/kanban.cards.move", {"cardId": task_id, "listId": to_section_id}
            )
            return True
        except Exception:
            return False

    def get_backend_type(self) -> str:
        """Return backend identifier."""
        return "kanban"

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate Kanban configuration."""
        if not self.base_url or not self.api_key:
            return False, "Kanban URL and API key required"

        try:
            self.list_boards()
            return True, None
        except Exception as e:
            return False, str(e)
