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
            json_data = response.json()
            # Most Kanban APIs wrap the response in a 'data' field
            if isinstance(json_data, dict) and "data" in json_data:
                return json_data["data"]
            return json_data

    def _map_priority(self, card_detail: Dict[str, Any]) -> Optional[str]:
        """Extract priority names from card details."""
        priorities = card_detail.get("priorities", [])
        if not priorities:
            # Fallback for old/other format
            p = card_detail.get("priority")
            if p is not None:
                priority_map = {0: "None", 1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
                return priority_map.get(p, "None")
            return None
        
        return ", ".join([p.get("name", "") for p in priorities if p.get("name")])

    def _fetch_and_format_comments(self, card_id: str) -> tuple[List[Dict[str, Any]], str]:
        """Fetch activities and format comments as a tree."""
        try:
            # API confirmed to use 'cardId' for activities
            activities = self._post("/api/kanban.cards.activities", {"cardId": card_id})
            
            if not activities:
                return [], ""
        except Exception as e:
            print(f"[DEBUG] Error fetching activities: {e}")
            return [], ""

        comments_list = []
        markdown_parts = []

        # Filter and process comment activities
        for activity in activities:
            if activity.get("name") == "kanban_cards.comment":
                comment_data = activity.get("data", {})
                actor = activity.get("actor", {})
                created_at = activity.get("createdAt", "")
                
                content = comment_data.get("comment", "")
                author = actor.get("name", "Unknown")
                replies = comment_data.get("replies", [])

                # Add to flat list for compatibility
                comments_list.append({
                    "content": content,
                    "author": author,
                    "created_at": created_at,
                    "replies": replies
                })

                # Format as tree in markdown
                markdown_parts.append(self._format_comment_node(content, author, created_at, replies, level=0))

        if markdown_parts:
            full_markdown = "\n\n---\n\n## Comments\n\n" + "\n".join(markdown_parts)
            return comments_list, full_markdown
        
        return comments_list, ""

    def _format_comment_node(self, content: str, author: str, created_at: str, replies: List[Dict[str, Any]], level: int) -> str:
        """Recursively format a comment and its replies."""
        indent = "  " * level
        timestamp = created_at.split("T")[0] if "T" in created_at else created_at
        
        markdown = f"{indent}- **{author}** [{timestamp}]: {content}\n"
        
        for reply in replies:
            r_content = reply.get("content", "")
            r_author = reply.get("createdBy", {}).get("name", "Unknown")
            r_created_at = reply.get("createdAt", "")
            r_replies = reply.get("replies", [])
            
            markdown += self._format_comment_node(r_content, r_author, r_created_at, r_replies, level + 1)
            
        return markdown

    def list_boards(self) -> List[BoardInfo]:
        """List all Kanban boards."""
        data = self._post("/api/kanban.boards.list")

        boards = []
        # data is now already unwrapped by _post
        for board in data if isinstance(data, list) else []:
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

        # Try to find cards in the specified section/list
        cards = []
        for lst in board_info.get("lists", []):
            if lst.get("id") == section_id:
                cards = lst.get("cards", [])
                break
        
        # Fallback to top-level cards if list-level cards not found
        if not cards:
            cards = board_info.get("cards", [])

        for card in cards:
            # Filter by list/column ID (if not already filtered)
            if card.get("listId") and card.get("listId") != section_id:
                continue

            # Get full task details using the helper method
            try:
                task_detail = self.get_task_detail(card["id"])
            except Exception:
                continue

            # Filter by labels if specified
            if label_filter and not any(
                lbl.lower() in label_filter for lbl in task_detail.labels
            ):
                continue

            task_items.append(task_detail)

        return task_items

    def get_task_detail(self, task_id: str) -> TaskItem:
        """Get detailed Kanban card information."""
        # Get card details
        card_detail = self._post("/api/kanban.cards.info", {"id": task_id})
        # card_detail is now already the inner data because of _post wrapper logic

        # Get comments and activities
        comments, comments_markdown = self._fetch_and_format_comments(task_id)

        # Build markdown description
        title = card_detail.get("title", "")
        description = card_detail.get("description", "")
        priority_str = self._map_priority(card_detail)
        due_date = card_detail.get("dueDate")
        card_labels = card_detail.get("tags", [])

        full_markdown = f"# {title}\n"
        full_markdown += "=" * (len(title) + 2) + "\n\n"

        if priority_str:
            full_markdown += f"**Priority:** {priority_str}\n"

        if due_date:
            full_markdown += f"**Due Date:** {due_date}\n"

        if card_labels:
            full_markdown += f"**Labels:** {', '.join(card_labels)}\n"
        
        full_markdown += "\n"

        if description:
            full_markdown += "## Description\n\n"
            full_markdown += description.strip() + "\n"

        if comments_markdown:
            full_markdown += "\n" + comments_markdown.strip() + "\n"

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
