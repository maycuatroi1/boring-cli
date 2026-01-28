"""Lark Suite backend implementation."""

from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx

from .base import BackendClient, TaskItem, BoardInfo, SectionInfo
from ..client import LarkClient, APIClient

LARK_BASE_URL = "https://open.larksuite.com/open-apis"


def rich_text_to_markdown(rich_text: Optional[dict]) -> str:
    """Convert Lark rich text format to Markdown.

    Args:
        rich_text: Lark rich text dictionary structure.

    Returns:
        Markdown-formatted string.
    """
    if not rich_text:
        return ""

    content = rich_text.get("content", [])
    markdown_lines = []

    for paragraph in content:
        line_parts = []
        is_code_block = paragraph.get("style", {}).get("codeBlock")
        is_quote = paragraph.get("style", {}).get("quote")

        for element in paragraph.get("elements", []):
            if "textRun" in element:
                text = element["textRun"].get("text", "")
                style = element["textRun"].get("style", {})

                if not is_code_block:
                    if style.get("bold"):
                        text = f"**{text}**"
                    if style.get("italic"):
                        text = f"*{text}*"
                    if style.get("strikethrough"):
                        text = f"~~{text}~~"
                    if style.get("codeInline"):
                        text = f"`{text}`"

                    link = style.get("link", {})
                    if link.get("url"):
                        text = f"[{text}]({link['url']})"

                line_parts.append(text)

            elif "mentionUser" in element:
                user_id = element["mentionUser"].get("userId", "")
                line_parts.append(f"@{user_id}")

            elif "file" in element:
                file_token = element["file"].get("fileToken", "")
                file_name = element["file"].get("name", file_token)
                line_parts.append(f"[File: {file_name}]")

            elif "image" in element:
                file_token = element["image"].get("fileToken", "")
                line_parts.append(f"![Image]({file_token})")

            elif "gallery" in element:
                images = element["gallery"].get("imageList", [])
                for img in images:
                    file_token = img.get("fileToken", "")
                    line_parts.append(f"![Image]({file_token})")

            elif "divider" in element:
                line_parts.append("\n---\n")

            elif "codeBlock" in element:
                language = element["codeBlock"].get("language", "")
                code = element["codeBlock"].get("text", "")
                line_parts.append(f"```{language}\n{code}\n```")

            elif "callout" in element:
                callout_content = element["callout"].get("content", {})
                callout_text = rich_text_to_markdown(callout_content)
                line_parts.append(f"> {callout_text}")

            elif "equation" in element:
                equation = element["equation"].get("content", "")
                line_parts.append(f"$${equation}$$")

            elif "docs_link" in element:
                url = element["docs_link"].get("url", "")
                title = element["docs_link"].get("title", url)
                line_parts.append(f"[{title}]({url})")

        paragraph_style = paragraph.get("style", {})
        heading_level = paragraph_style.get("headingLevel", 0)

        line = "".join(line_parts)

        if is_code_block:
            language = paragraph_style.get("codeLanguage", "")
            line = f"```{language}\n{line}\n```"
        elif is_quote:
            line = f"> {line}"
        elif heading_level:
            line = f"{'#' * heading_level} {line}"

        if paragraph_style.get("list"):
            list_type = paragraph_style["list"].get("type")
            indent_level = paragraph_style["list"].get("indentLevel", 0)
            indent = "  " * indent_level
            if list_type == "number":
                line = f"{indent}1. {line}"
            else:
                line = f"{indent}- {line}"

        markdown_lines.append(line)

    return "\n".join(markdown_lines)


class LarkBackend(BackendClient):
    """Backend implementation for Lark Suite task management."""

    def __init__(
        self,
        server_url: Optional[str] = None,
        jwt_token: Optional[str] = None,
        lark_token: Optional[str] = None,
        tasklist_guid: Optional[str] = None,
        section_guid: Optional[str] = None,
        solved_section_guid: Optional[str] = None,
    ):
        """Initialize Lark backend.

        Args:
            server_url: Boring Agents API server URL.
            jwt_token: JWT token for Boring API authentication.
            lark_token: Lark access token for API calls.
            tasklist_guid: Default tasklist GUID.
            section_guid: Default section GUID for in-progress tasks.
            solved_section_guid: Section GUID for solved tasks.
        """
        self.server_url = server_url
        self.jwt_token = jwt_token
        self.lark_token = lark_token
        self.tasklist_guid = tasklist_guid
        self.section_guid = section_guid
        self.solved_section_guid = solved_section_guid
        self._lark_client = LarkClient(access_token=lark_token) if lark_token else None

    def _get_lark_client(self) -> LarkClient:
        """Get Lark client instance."""
        if not self._lark_client:
            raise Exception("Lark token not configured. Run 'boring setup' first.")
        return self._lark_client

    def list_boards(self) -> List[BoardInfo]:
        """List all Lark tasklists."""
        client = self._get_lark_client()
        result = client.list_tasklists(page_size=50)

        boards = []
        for item in result.get("data", {}).get("items", []):
            boards.append(BoardInfo(id=item["guid"], name=item["name"]))

        return boards

    def get_board_info(self, board_id: str) -> Dict[str, Any]:
        """Get Lark tasklist details."""
        client = self._get_lark_client()
        return client.get_tasklist(board_id)

    def list_sections(self, board_id: str) -> List[SectionInfo]:
        """List all sections in a Lark tasklist."""
        client = self._get_lark_client()
        result = client.list_sections(board_id, page_size=50)

        sections = []
        for item in result.get("data", {}).get("items", []):
            sections.append(
                SectionInfo(id=item["guid"], name=item["name"], board_id=board_id)
            )

        return sections

    def list_tasks(
        self, section_id: str, labels: Optional[List[str]] = None
    ) -> List[TaskItem]:
        """List all tasks in a Lark section."""
        client = self._get_lark_client()
        result = client.list_tasks_in_section(section_id, page_size=50)

        task_items = []
        label_filter = set(lbl.lower() for lbl in labels) if labels else None

        for item in result.get("data", {}).get("items", []):
            task_guid = item.get("guid")

            # Get full task details
            task_detail = self.get_task_detail(task_guid)

            # Filter by labels if specified
            if label_filter and not any(
                lbl.lower() in label_filter for lbl in task_detail.labels
            ):
                continue

            task_items.append(task_detail)

        return task_items

    def get_task_detail(self, task_id: str) -> TaskItem:
        """Get detailed Lark task information."""
        client = self._get_lark_client()

        # Get task details
        task_detail = client.get_task(task_id)
        task_data = task_detail.get("data", {}).get("task", {})

        # Extract basic info
        title = task_data.get("summary", "No title")

        # Convert description to markdown
        description_data = task_data.get("description")
        if isinstance(description_data, dict):
            description = rich_text_to_markdown(description_data)
        elif isinstance(description_data, str):
            description = description_data
        else:
            description = ""

        # Build full markdown with metadata
        full_markdown = f"# {title}\n\n"

        # Add priority
        priority = task_data.get("priority")
        if priority is not None:
            priority_map = {0: "None", 1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
            priority_str = priority_map.get(priority, "None")
            full_markdown += f"**Priority:** {priority_str}\n\n"
        else:
            priority_str = None

        # Add due date
        due = task_data.get("due")
        due_date = None
        if due:
            due_date = due.get("date", "")
            full_markdown += f"**Due:** {due_date}\n\n"

        if description:
            full_markdown += "---\n\n"
            full_markdown += description

        # Get labels from custom fields
        task_labels = [
            m.get("name", "") for m in task_data.get("custom_fields", [])
        ]

        # Get comments
        try:
            comments_data = client.list_task_comments(task_id)
            comments = []
            if comments_data:
                full_markdown += "\n\n---\n\n## Comments\n\n"
                for comment in comments_data:
                    comment_content = comment.get("content", "")
                    created_at = comment.get("created_at", "")

                    if created_at:
                        try:
                            ts = int(created_at) / 1000
                            dt = datetime.fromtimestamp(ts)
                            full_markdown += f"### {dt.strftime('%Y-%m-%d %H:%M')}\n\n"
                            comments.append({
                                "content": comment_content,
                                "created_at": dt.strftime('%Y-%m-%d %H:%M')
                            })
                        except Exception:
                            full_markdown += "### Comment\n\n"
                            comments.append({"content": comment_content, "created_at": ""})
                    else:
                        comments.append({"content": comment_content, "created_at": ""})

                    full_markdown += f"{comment_content}\n\n"
        except Exception:
            comments = []

        return TaskItem(
            id=task_id,
            title=title,
            description=full_markdown,
            priority=priority_str,
            due_date=due_date,
            labels=task_labels,
            comments=comments,
        )

    def move_task(
        self, task_id: str, from_section_id: str, to_section_id: str
    ) -> bool:
        """Move a Lark task to a different section."""
        try:
            api_client = APIClient(base_url=self.server_url, token=self.jwt_token)
            api_client.solve_task(
                task_guid=task_id,
                tasklist_guid=self.tasklist_guid,
                section_guid=to_section_id,
            )
            return True
        except Exception:
            return False

    def get_backend_type(self) -> str:
        """Return backend identifier."""
        return "lark"

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate Lark configuration."""
        if not self.lark_token:
            return False, "Lark token not configured"

        try:
            self.list_boards()
            return True, None
        except Exception as e:
            return False, str(e)
