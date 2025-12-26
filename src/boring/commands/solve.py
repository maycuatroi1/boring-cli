"""Solve command for Boring CLI."""

import os
import shutil

import click
from rich.console import Console

from .. import config
from ..client import APIClient

console = Console()


def get_task_folders(bugs_dir: str) -> list:
    """Get all task folders from the bugs directory."""
    folders = []
    if not os.path.exists(bugs_dir):
        return folders
    for name in os.listdir(bugs_dir):
        path = os.path.join(bugs_dir, name)
        # UUID format check
        if os.path.isdir(path) and len(name) == 36 and name.count("-") == 4:
            folders.append((name, path))
    return folders


@click.command()
@click.option("--keep", is_flag=True, help="Keep local folders after solving")
def solve(keep: bool):
    """Move completed tasks to Solved section in Lark."""
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    bugs_dir = config.get_bugs_dir()
    tasklist_guid = config.get_tasklist_guid()
    solved_section_guid = config.get_solved_section_guid()

    if not bugs_dir:
        console.print("[bold red]Bugs directory not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    if not tasklist_guid or not solved_section_guid:
        console.print(
            "[bold red]Tasklist GUID and Solved Section GUID required.[/bold red] "
            "Run 'boring setup' first."
        )
        raise click.Abort()

    task_folders = get_task_folders(bugs_dir)

    if not task_folders:
        console.print("[yellow]No tasks found in bugs folder.[/yellow]")
        return

    console.print(f"[bold]Found {len(task_folders)} task(s) to move to Solved[/bold]\n")

    client = APIClient()
    success_count = 0

    for task_guid, folder_path in task_folders:
        try:
            result = client.solve_task(
                task_guid=task_guid,
                tasklist_guid=tasklist_guid,
                section_guid=solved_section_guid,
            )

            if result.get("success"):
                console.print(f"[green]OK[/green] - {task_guid}")
                if not keep:
                    shutil.rmtree(folder_path)
                success_count += 1
            else:
                console.print(f"[red]FAIL[/red] - {task_guid}: {result.get('message')}")
        except Exception as e:
            console.print(f"[red]ERROR[/red] - {task_guid}: {e}")

    console.print(
        f"\n[bold green]Done![/bold green] Moved {success_count}/{len(task_folders)} task(s) to Solved."
    )
