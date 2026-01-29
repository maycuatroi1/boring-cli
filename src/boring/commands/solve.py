"""Solve command for Boring CLI."""

import os
import shutil

import click
from rich.console import Console

from .. import config
from ..backends import get_backend

console = Console()


def get_task_folders(bugs_dir: str) -> list:
    """Get all task folders from the bugs directory."""
    folders = []
    if not os.path.exists(bugs_dir):
        return folders
    for name in os.listdir(bugs_dir):
        path = os.path.join(bugs_dir, name)
        # Check if it's a directory and looks like an ID (could be UUID or other format)
        if os.path.isdir(path) and name.strip():
            folders.append((name, path))
    return folders


@click.command()
@click.option("--keep", is_flag=True, help="Keep local folders after solving")
def solve(keep: bool):
    """Move completed tasks/cards to Solved/Done section."""
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    bugs_dir = config.get_bugs_dir()
    backend_type = config.get_backend_type()

    # Get section IDs based on backend type
    if backend_type == "lark":
        from_section_id = config.get_section_guid()
        to_section_id = config.get_solved_section_guid()
        item_label = "task"
    elif backend_type == "kanban":
        from_section_id = config.get_kanban_list_id()
        to_section_id = config.get_kanban_done_list_id()
        item_label = "card"
    else:
        console.print(f"[bold red]Unknown backend type:[/bold red] {backend_type}")
        raise click.Abort()

    if not bugs_dir:
        console.print("[bold red]Bugs directory not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    if not from_section_id or not to_section_id:
        console.print(
            "[bold red]Section IDs required.[/bold red] "
            "Run 'boring setup' first."
        )
        raise click.Abort()

    task_folders = get_task_folders(bugs_dir)

    if not task_folders:
        console.print(f"[yellow]No {item_label}s found in bugs folder.[/yellow]")
        return

    console.print(f"[bold]Found {len(task_folders)} {item_label}(s) to move to Done/Solved[/bold]\n")

    try:
        backend = get_backend()
    except Exception as e:
        console.print(f"[bold red]Failed to initialize backend:[/bold red] {e}")
        raise click.Abort()

    success_count = 0

    for task_id, folder_path in task_folders:
        try:
            success = backend.move_task(
                task_id=task_id,
                from_section_id=from_section_id,
                to_section_id=to_section_id,
            )

            if success:
                console.print(f"[green]OK[/green] - {task_id}")
                if not keep:
                    shutil.rmtree(folder_path)
                success_count += 1
            else:
                console.print(f"[red]FAIL[/red] - {task_id}: Move operation failed")
        except Exception as e:
            console.print(f"[red]ERROR[/red] - {task_id}: {e}")

    console.print(
        f"\n[bold green]Done![/bold green] Moved {success_count}/{len(task_folders)} {item_label}(s) to Done/Solved."
    )
