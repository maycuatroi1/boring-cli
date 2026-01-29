"""Download command for Boring CLI."""

import os
from pathlib import Path

import click
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
            console.print(f"[bold red]Failed to fetch {item_label}s:[/bold red] {e}")
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

            md_path = task_dir / "description.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(task_item.description)

            downloaded_count += 1
            progress.advance(download_task)
            console.print(f"  [dim]Saved: {task_item.title[:50]}...[/dim]")

    console.print(f"\n[bold green]Done![/bold green] {downloaded_count} {item_label}(s) saved to '{bugs_dir}/'")
