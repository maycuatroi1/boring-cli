"""Download command for Boring CLI."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .. import config
from ..client import LarkClient, APIClient

console = Console()


def refresh_lark_token() -> Optional[str]:
    try:
        client = APIClient()
        result = client.get_lark_token()
        if "access_token" in result:
            config.set_lark_token(result["access_token"])
            return result["access_token"]
    except Exception:
        pass
    return None


def rich_text_to_markdown(rich_text: Optional[dict]) -> str:
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
    label_filter = set(lbl.strip().lower() for lbl in labels.split(",")) if labels else None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching tasks from Lark...", total=None)

        try:
            result = client.list_tasks_in_section(section_guid)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (400, 401):
                progress.update(task, description="Token expired, refreshing...")
                new_token = refresh_lark_token()
                if new_token:
                    console.print("[yellow]Token refreshed successfully[/yellow]")
                    client = LarkClient(access_token=new_token)
                    try:
                        result = client.list_tasks_in_section(section_guid)
                    except Exception as retry_e:
                        console.print(f"[bold red]Failed after token refresh:[/bold red] {retry_e}")
                        raise click.Abort()
                else:
                    console.print("[bold red]Token expired and refresh failed.[/bold red] Run 'boring setup' again.")
                    raise click.Abort()
            else:
                console.print(f"[bold red]Failed to fetch tasks:[/bold red] {e}")
                raise click.Abort()
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

        token_refreshed = False
        for task_item in task_items:
            task_guid = task_item.get("guid")

            progress.update(task, description=f"Fetching task {task_guid[:8]}...")

            try:
                task_detail = client.get_task(task_guid)
                task_data = task_detail.get("data", {}).get("task", {})
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 401) and not token_refreshed:
                    new_token = refresh_lark_token()
                    if new_token:
                        client = LarkClient(access_token=new_token)
                        token_refreshed = True
                        try:
                            task_detail = client.get_task(task_guid)
                            task_data = task_detail.get("data", {}).get("task", {})
                        except Exception:
                            progress.advance(task)
                            continue
                    else:
                        console.print(f"[yellow]Failed to fetch task {task_guid}: token expired[/yellow]")
                        progress.advance(task)
                        continue
                else:
                    console.print(f"[yellow]Failed to fetch task {task_guid}: {e}[/yellow]")
                    progress.advance(task)
                    continue
            except Exception as e:
                console.print(f"[yellow]Failed to fetch task {task_guid}: {e}[/yellow]")
                progress.advance(task)
                continue

            summary = task_data.get("summary", "No title")

            # Filter by labels if specified
            if label_filter:
                task_labels = [m.get("name", "").lower() for m in task_data.get("custom_fields", [])]
                if not any(lbl in label_filter for lbl in task_labels):
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

            try:
                comments = client.list_task_comments(task_guid)
                if comments:
                    full_markdown += "\n\n---\n\n## Comments\n\n"
                    for comment in comments:
                        comment_content = comment.get("content", "")
                        created_at = comment.get("created_at", "")
                        if created_at:
                            try:
                                ts = int(created_at) / 1000
                                dt = datetime.fromtimestamp(ts)
                                full_markdown += f"### {dt.strftime('%Y-%m-%d %H:%M')}\n\n"
                            except Exception:
                                full_markdown += "### Comment\n\n"
                        full_markdown += f"{comment_content}\n\n"
            except Exception:
                pass

            task_dir = Path(bugs_dir) / task_guid
            task_dir.mkdir(parents=True, exist_ok=True)

            md_path = task_dir / "description.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(full_markdown)

            downloaded_count += 1
            progress.advance(task)
            console.print(f"  [dim]Saved: {summary[:50]}...[/dim]")

    console.print(f"\n[bold green]Done![/bold green] {downloaded_count} task(s) saved to '{bugs_dir}/'")
