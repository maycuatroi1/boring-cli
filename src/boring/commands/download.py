"""Download command for Boring CLI."""

import base64
import os
import re
from pathlib import Path
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .. import config
from ..client import LarkClient

console = Console()


def rich_text_to_markdown(rich_text: Optional[dict]) -> str:
    """Convert Lark rich text format to markdown."""
    if not rich_text:
        return ""

    content = rich_text.get("content", [])
    markdown_lines = []

    for paragraph in content:
        line_parts = []
        for element in paragraph.get("elements", []):
            if "textRun" in element:
                text = element["textRun"].get("text", "")
                style = element["textRun"].get("style", {})

                # Apply styles
                if style.get("bold"):
                    text = f"**{text}**"
                if style.get("italic"):
                    text = f"*{text}*"
                if style.get("strikethrough"):
                    text = f"~~{text}~~"
                if style.get("codeInline"):
                    text = f"`{text}`"

                # Handle links
                link = style.get("link", {})
                if link.get("url"):
                    text = f"[{text}]({link['url']})"

                line_parts.append(text)

            elif "mentionUser" in element:
                user_id = element["mentionUser"].get("userId", "")
                line_parts.append(f"@{user_id}")

            elif "file" in element:
                file_token = element["file"].get("fileToken", "")
                line_parts.append(f"[File: {file_token}]")

        paragraph_style = paragraph.get("style", {})
        heading_level = paragraph_style.get("headingLevel", 0)

        line = "".join(line_parts)

        if heading_level:
            line = f"{'#' * heading_level} {line}"

        # Handle list items
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


def download_image(url: str, headers: dict) -> Optional[bytes]:
    """Download image from URL."""
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.content
    except Exception:
        return None


@click.command()
@click.option("--labels", default=None, help="Comma-separated labels to filter")
@click.option("--section", default=None, help="Section GUID to filter (overrides config)")
@click.option("--dir", "bugs_dir_option", default=None, help="Output directory (overrides config)")
def download(labels: str, section: str, bugs_dir_option: str):
    """Download tasks from Lark and save as markdown files."""
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    bugs_dir = bugs_dir_option or config.get_bugs_dir()
    section_guid = section or config.get_section_guid()

    if not bugs_dir:
        console.print("[bold red]Bugs directory not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    if not section_guid:
        console.print("[bold red]Section GUID not configured.[/bold red] Run 'boring setup' or use --section.")
        raise click.Abort()

    lark_token = config.get_lark_token()
    if not lark_token:
        console.print("[bold red]Lark token not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    console.print(f"[bold]Downloading tasks to:[/bold] [cyan]{bugs_dir}[/cyan]")
    console.print(f"[dim]Using section: {section_guid}[/dim]")
    if labels:
        console.print(f"[dim]Filtering by labels: {labels}[/dim]")

    client = LarkClient()
    label_filter = set(l.strip().lower() for l in labels.split(",")) if labels else None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching tasks from Lark...", total=None)

        try:
            # Get tasks in section directly from Lark API
            result = client.list_tasks_in_section(section_guid)
        except Exception as e:
            console.print(f"[bold red]Failed to fetch tasks:[/bold red] {e}")
            raise click.Abort()

        progress.update(task, description="Processing tasks...")

    task_items = result.get("data", {}).get("items", [])

    if not task_items:
        console.print("[yellow]No tasks found in section.[/yellow]")
        return

    console.print(f"\n[bold green]Found {len(task_items)} task(s) in section[/bold green]\n")

    os.makedirs(bugs_dir, exist_ok=True)

    downloaded_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading tasks...", total=len(task_items))

        for task_item in task_items:
            task_guid = task_item.get("guid")

            progress.update(task, description=f"Fetching task {task_guid[:8]}...")

            try:
                # Get full task details
                task_detail = client.get_task(task_guid)
                task_data = task_detail.get("data", {}).get("task", {})
            except Exception as e:
                console.print(f"[yellow]Failed to fetch task {task_guid}: {e}[/yellow]")
                progress.advance(task)
                continue

            summary = task_data.get("summary", "No title")

            # Filter by labels if specified
            if label_filter:
                task_labels = [m.get("name", "").lower() for m in task_data.get("custom_fields", [])]
                if not any(l in label_filter for l in task_labels):
                    progress.advance(task)
                    continue

            # Convert description to markdown
            description = task_data.get("description")
            if isinstance(description, dict):
                markdown_content = rich_text_to_markdown(description)
            elif isinstance(description, str):
                markdown_content = description
            else:
                markdown_content = ""

            # Build full markdown with metadata
            full_markdown = f"# {summary}\n\n"

            # Add metadata
            priority = task_data.get("priority")
            if priority:
                priority_map = {0: "None", 1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
                full_markdown += f"**Priority:** {priority_map.get(priority, priority)}\n\n"

            due = task_data.get("due")
            if due:
                full_markdown += f"**Due:** {due.get('date', '')}\n\n"

            if markdown_content:
                full_markdown += "---\n\n"
                full_markdown += markdown_content

            # Save to file
            task_dir = Path(bugs_dir) / task_guid
            task_dir.mkdir(parents=True, exist_ok=True)

            md_path = task_dir / "description.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(full_markdown)

            # Download attachments if any
            attachments = task_data.get("attachments", [])
            for i, attachment in enumerate(attachments, 1):
                file_token = attachment.get("file_token")
                if file_token:
                    # Note: Downloading attachments requires additional API calls
                    # This is a placeholder for future implementation
                    pass

            downloaded_count += 1
            progress.advance(task)
            console.print(f"  [dim]Saved: {summary[:50]}...[/dim]")

    console.print(f"\n[bold green]Done![/bold green] {downloaded_count} task(s) saved to '{bugs_dir}/'")
