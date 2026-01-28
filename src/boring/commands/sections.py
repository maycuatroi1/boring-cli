"""Sections command for Boring CLI."""

import click
from rich.console import Console
from rich.table import Table

from .. import config
from ..backends import get_backend

console = Console()


@click.command()
def sections():
    """List all boards/tasklists and sections/columns."""
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    backend_type = config.get_backend_type()
    board_label = "Tasklist" if backend_type == "lark" else "Board"
    section_label = "Section" if backend_type == "lark" else "Column"

    console.print(f"[bold]Fetching {board_label.lower()}s...[/bold]\n")

    try:
        backend = get_backend()
    except Exception as e:
        console.print(f"[bold red]Failed to initialize backend:[/bold red] {e}")
        raise click.Abort()

    try:
        boards = backend.list_boards()

        if not boards:
            console.print(f"[yellow]No {board_label.lower()}s found.[/yellow]")
            return

        for board in boards:
            console.print(f"[bold cyan]{board_label}:[/bold cyan] {board.name}")
            console.print(f"[dim]ID: {board.id}[/dim]\n")

            try:
                sections = backend.list_sections(board.id)

                if not sections:
                    console.print(f"  [dim]No {section_label.lower()}s[/dim]\n")
                    continue

                table = Table(show_header=True, header_style="bold")
                table.add_column(f"{section_label} Name", style="green")
                table.add_column("ID", style="dim")

                for section in sections:
                    table.add_row(section.name, section.id)

                console.print(table)
                console.print()

            except Exception as e:
                console.print(f"  [yellow]Error fetching {section_label.lower()}s: {e}[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Failed to fetch {board_label.lower()}s:[/bold red] {e}")
        raise click.Abort()
