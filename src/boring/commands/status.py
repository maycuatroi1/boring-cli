"""Status command for Boring CLI."""

import click
from rich.console import Console
from rich.table import Table

from .. import config

console = Console()


@click.command()
def status():
    """Show current configuration status."""
    cfg = config.load_config()

    table = Table(title="Boring CLI Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    # Server URL
    server_url = cfg.get("server_url", "")
    table.add_row(
        "Server URL",
        server_url or "[dim]Not set[/dim]",
        "[green]OK[/green]" if server_url else "[red]Missing[/red]",
    )

    # JWT Token
    jwt_token = cfg.get("jwt_token", "")
    token_display = f"{jwt_token[:20]}..." if jwt_token else "[dim]Not set[/dim]"
    table.add_row(
        "JWT Token",
        token_display,
        "[green]OK[/green]" if jwt_token else "[red]Missing[/red]",
    )

    # Bugs Directory
    bugs_dir = cfg.get("bugs_dir", "")
    table.add_row(
        "Bugs Directory",
        bugs_dir or "[dim]Not set[/dim]",
        "[green]OK[/green]" if bugs_dir else "[red]Missing[/red]",
    )

    # Tasklist GUID
    tasklist_guid = cfg.get("tasklist_guid", "")
    table.add_row(
        "Tasklist GUID",
        tasklist_guid or "[dim]Not set[/dim]",
        "[green]OK[/green]" if tasklist_guid else "[yellow]Optional[/yellow]",
    )

    # Section GUID
    section_guid = cfg.get("section_guid", "")
    table.add_row(
        "Section GUID",
        section_guid or "[dim]Not set[/dim]",
        "[green]OK[/green]" if section_guid else "[yellow]Optional[/yellow]",
    )

    # Solved Section GUID
    solved_section_guid = cfg.get("solved_section_guid", "")
    table.add_row(
        "Solved Section GUID",
        solved_section_guid or "[dim]Not set[/dim]",
        "[green]OK[/green]" if solved_section_guid else "[yellow]Optional[/yellow]",
    )

    console.print()
    console.print(table)
    console.print()

    if config.is_configured():
        console.print("[bold green]CLI is properly configured![/bold green]")
    else:
        console.print(
            "[bold yellow]CLI is not fully configured.[/bold yellow] "
            "Run 'boring setup' to complete configuration."
        )

    console.print(f"\n[dim]Config file: {config.CONFIG_FILE}[/dim]")
