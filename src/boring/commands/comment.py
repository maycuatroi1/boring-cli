import sys

import click
from rich.console import Console

from .. import config
from ..backends import get_backend

console = Console()


@click.command()
@click.argument("task_id")
@click.argument("message", required=False)
def comment(task_id: str, message: str):
    """Post a comment on a task/card.

    \b
    Examples:
      boring comment TASK_ID "Your comment here"
      echo "multi-line comment" | boring comment TASK_ID
      boring comment TASK_ID < fix-summary.md
    """
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    if not message:
        if not sys.stdin.isatty():
            message = sys.stdin.read().strip()
        if not message:
            console.print("[bold red]No comment provided.[/bold red] Pass as argument or pipe via stdin.")
            raise click.Abort()

    try:
        backend = get_backend()
    except Exception as e:
        console.print(f"[bold red]Failed to initialize backend:[/bold red] {e}")
        raise click.Abort()

    try:
        success = backend.add_comment(task_id, message)
        if success:
            console.print(f"[green]Comment posted on {task_id}[/green]")
        else:
            console.print(f"[red]Failed to post comment on {task_id}[/red]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
