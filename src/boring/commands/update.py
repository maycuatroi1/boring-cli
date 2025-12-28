"""Update command for Boring CLI."""

import subprocess
import sys

import click
from rich.console import Console

from ..version_check import check_for_updates

console = Console()


@click.command()
@click.option("--force", is_flag=True, help="Force update even if already on latest version")
def update(force: bool):
    """Update Boring CLI to the latest version."""
    console.print("[bold]Checking for updates...[/bold]")

    update_available, latest, current = check_for_updates()

    if latest is None:
        console.print("[red]Failed to check for updates. Please try again later.[/red]")
        raise click.Abort()

    console.print(f"Current version: [cyan]{current}[/cyan]")
    console.print(f"Latest version:  [cyan]{latest}[/cyan]")

    if not update_available and not force:
        console.print("\n[green]✓ You are already on the latest version![/green]")
        return

    if not update_available and force:
        console.print("\n[yellow]Forcing reinstall...[/yellow]")

    console.print(f"\n[bold]Updating boring-cli to {latest}...[/bold]\n")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "boring-cli"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✓ Update successful![/green]")
            console.print(f"[dim]Updated from {current} → {latest}[/dim]")
        else:
            console.print("[red]Update failed:[/red]")
            console.print(result.stderr)
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Update failed:[/red] {e}")
        raise click.Abort()
