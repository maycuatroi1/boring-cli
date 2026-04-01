"""Download command for Boring CLI."""

import os
import re
from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .. import config
from ..backends import get_backend

console = Console()


@click.command()
@click.option("--labels", default=None, help="Comma-separated labels to filter")
@click.option("--section", default=None, help="Section ID to filter (overrides config)")
@click.option("--dir", "bugs_dir_option", default=None, help="Output directory (overrides config)")
def download(labels: str, section: str, bugs_dir_option: str):
    """Download tasks/cards and save as markdown files."""
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    bugs_dir = bugs_dir_option or config.get_bugs_dir()
    backend_type = config.get_backend_type()

    # Get section ID based on backend type
    if backend_type == "lark":
        section_id = section or config.get_section_guid()
        item_label = "task"
    elif backend_type == "kanban":
        section_id = section or config.get_kanban_list_id()
        item_label = "card"
    else:
        console.print(f"[bold red]Unknown backend type:[/bold red] {backend_type}")
        raise click.Abort()

    if not bugs_dir:
        console.print("[bold red]Bugs directory not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    if not section_id:
        console.print(f"[bold red]Section ID not configured.[/bold red] Run 'boring setup' or use --section.")
        raise click.Abort()

    console.print(f"[bold]Downloading {item_label}s to:[/bold] [cyan]{bugs_dir}[/cyan]")
    console.print(f"[dim]Using section: {section_id}[/dim]")
    if labels:
        console.print(f"[dim]Filtering by labels: {labels}[/dim]")

    try:
        backend = get_backend()
    except Exception as e:
        console.print(f"[bold red]Failed to initialize backend:[/bold red] {e}")
        raise click.Abort()

    label_filter = [lbl.strip() for lbl in labels.split(",")] if labels else None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Fetching {item_label}s...", total=None)

        try:
            tasks = backend.list_tasks(section_id=section_id, labels=label_filter)
        except Exception as e:
            error_msg = str(e)
            console.print(f"[bold red]Failed to fetch {item_label}s:[/bold red] {error_msg}")
            if "re-authorization" in error_msg.lower() or "unauthorized" in error_msg.lower():
                console.print("[yellow]Try running 'boring setup' to re-authorize.[/yellow]")
            raise click.Abort()

        progress.update(task, description=f"Processing {item_label}s...")

    if not tasks:
        console.print(f"[yellow]No {item_label}s found in section.[/yellow]")
        return

    console.print(f"\n[bold green]Found {len(tasks)} {item_label}(s) in section[/bold green]\n")

    os.makedirs(bugs_dir, exist_ok=True)

    downloaded_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        download_task = progress.add_task(f"Downloading {item_label}s...", total=len(tasks))

        for task_item in tasks:
            progress.update(download_task, description=f"Saving {task_item.id[:8]}...")

            task_dir = Path(bugs_dir) / task_item.id
            task_dir.mkdir(parents=True, exist_ok=True)

            description = task_item.description
            if task_item.attachments:
                images_dir = task_dir / "images"
                images_dir.mkdir(parents=True, exist_ok=True)
                for idx, att in enumerate(task_item.attachments):
                    att_name = att.get("name", f"image_{idx}")
                    att_url = att.get("url", "")
                    if att_url:
                        try:
                            with httpx.Client(timeout=120, follow_redirects=True) as http_client:
                                resp = http_client.get(att_url)
                                resp.raise_for_status()
                                file_path = images_dir / att_name
                                with open(file_path, "wb") as img_f:
                                    img_f.write(resp.content)
                                rel_path = f"images/{att_name}"
                                description = description.replace(
                                    "[Image]", f"![{att_name}]({rel_path})", 1
                                )
                        except Exception:
                            pass

            md_path = task_dir / "description.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(description)

            downloaded_count += 1
            progress.advance(download_task)
            console.print(f"  [dim]Saved: {task_item.title[:50]}...[/dim]")

    console.print(f"\n[bold green]Done![/bold green] {downloaded_count} {item_label}(s) saved to '{bugs_dir}/'")
