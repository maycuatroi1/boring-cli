"""Main entry point for Boring CLI."""

import click
from rich.console import Console

from . import __version__
from .commands.download import download
from .commands.sections import sections
from .commands.setup import setup
from .commands.solve import solve
from .commands.status import status
from .commands.update import update
from .version_check import check_for_updates

console = Console()


def show_update_warning():
    """Check for updates and show warning if available."""
    try:
        update_available, latest, current = check_for_updates()
        if update_available and latest:
            console.print(
                f"[yellow]⚠ Update available:[/yellow] {current} → [green]{latest}[/green]"
            )
            console.print(
                "[dim]Run:[/dim] [cyan]pip install --upgrade boring-cli[/cyan]\n"
            )
    except Exception:
        pass  # Silently ignore any errors during version check


@click.group()
@click.version_option(version=__version__, prog_name="boring")
def cli():
    """Boring CLI - Manage Lark tasks from the command line.

    \b
    Quick start:
      boring setup      Configure and login to Lark
      boring download   Download tasks to local folder
      boring solve      Move completed tasks to Solved
      boring status     Show current configuration
      boring sections   List tasklists and sections
      boring update     Update CLI to latest version
    """
    show_update_warning()


cli.add_command(setup)
cli.add_command(download)
cli.add_command(solve)
cli.add_command(status)
cli.add_command(sections)
cli.add_command(update)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
