"""Download command for Boring CLI."""

import base64
import os
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .. import config
from ..client import APIClient

console = Console()


@click.command()
@click.option("--labels", default=None, help="Comma-separated labels to filter")
def download(labels: str):
    """Download tasks from Lark and save as markdown files."""
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    bugs_dir = config.get_bugs_dir()
    section_guid = config.get_section_guid()

    if not bugs_dir:
        console.print("[bold red]Bugs directory not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    console.print(f"[bold]Downloading tasks to:[/bold] [cyan]{bugs_dir}[/cyan]")
    if section_guid:
        console.print(f"[dim]Filtering by section: {section_guid}[/dim]")
    if labels:
        console.print(f"[dim]Filtering by labels: {labels}[/dim]")

    client = APIClient()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching tasks from server...", total=None)

        try:
            result = client.download_tasks(labels=labels, section_guid=section_guid)
        except Exception as e:
            console.print(f"[bold red]Failed to download tasks:[/bold red] {e}")
            raise click.Abort()

        progress.update(task, description="Processing tasks...")

    tasks = result.get("tasks", [])
    count = result.get("count", 0)

    if count == 0:
        console.print("[yellow]No tasks found matching criteria.[/yellow]")
        return

    console.print(f"\n[bold green]Found {count} task(s)[/bold green]\n")

    os.makedirs(bugs_dir, exist_ok=True)

    for i, task_data in enumerate(tasks, 1):
        guid = task_data.get("guid")
        summary = task_data.get("summary", "No title")[:50]
        console.print(f"[{i}/{count}] Processing: [cyan]{summary}[/cyan]...")

        task_dir = Path(bugs_dir) / guid
        task_dir.mkdir(parents=True, exist_ok=True)

        md_path = task_dir / "description.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(task_data.get("markdown_content", ""))

        for img in task_data.get("images", []):
            img_index = img.get("index", 1)
            img_data = img.get("data")
            if img_data:
                img_bytes = base64.b64decode(img_data)
                img_path = task_dir / f"image_{img_index}.jpg"
                with open(img_path, "wb") as f:
                    f.write(img_bytes)

        console.print(f"  [dim]Saved to {task_dir}/description.md[/dim]")

    console.print(f"\n[bold green]Done![/bold green] {count} task(s) saved to '{bugs_dir}/'")
