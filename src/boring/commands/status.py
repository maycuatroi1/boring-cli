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
    backend_type = cfg.get("backend_type", "lark")

    table = Table(title="Boring CLI Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    # Backend Type
    table.add_row(
        "Backend Type",
        backend_type,
        "[green]OK[/green]",
    )

    # Bugs Directory
    bugs_dir = cfg.get("bugs_dir", "")
    table.add_row(
        "Bugs Directory",
        bugs_dir or "[dim]Not set[/dim]",
        "[green]OK[/green]" if bugs_dir else "[red]Missing[/red]",
    )

    # Backend-specific configuration
    if backend_type == "lark":
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

        # Lark Token
        lark_token = cfg.get("lark_token", "")
        lark_token_display = f"{lark_token[:20]}..." if lark_token else "[dim]Not set[/dim]"
        table.add_row(
            "Lark Token",
            lark_token_display,
            "[green]OK[/green]" if lark_token else "[yellow]Optional[/yellow]",
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

    elif backend_type == "kanban":
        # Kanban Base URL
        kanban_base_url = cfg.get("kanban_base_url", "")
        table.add_row(
            "Kanban Base URL",
            kanban_base_url or "[dim]Not set[/dim]",
            "[green]OK[/green]" if kanban_base_url else "[red]Missing[/red]",
        )

        # Kanban API Key
        kanban_api_key = cfg.get("kanban_api_key", "")
        api_key_display = f"{kanban_api_key[:20]}..." if kanban_api_key else "[dim]Not set[/dim]"
        table.add_row(
            "Kanban API Key",
            api_key_display,
            "[green]OK[/green]" if kanban_api_key else "[red]Missing[/red]",
        )

        # Kanban Board ID
        kanban_board_id = cfg.get("kanban_board_id", "")
        table.add_row(
            "Kanban Board ID",
            kanban_board_id or "[dim]Not set[/dim]",
            "[green]OK[/green]" if kanban_board_id else "[yellow]Optional[/yellow]",
        )

        # Kanban List ID (in-progress)
        kanban_list_id = cfg.get("kanban_list_id", "")
        table.add_row(
            "Kanban List ID (In-Progress)",
            kanban_list_id or "[dim]Not set[/dim]",
            "[green]OK[/green]" if kanban_list_id else "[yellow]Optional[/yellow]",
        )

        # Kanban Done List ID
        kanban_done_list_id = cfg.get("kanban_done_list_id", "")
        table.add_row(
            "Kanban Done List ID",
            kanban_done_list_id or "[dim]Not set[/dim]",
            "[green]OK[/green]" if kanban_done_list_id else "[yellow]Optional[/yellow]",
        )

    console.print()
    console.print(table)
    console.print()

    if config.is_configured():
        console.print("[bold green]CLI is properly configured![/bold green]")

        # Try to validate backend connection
        try:
            from ..backends import get_backend
            backend = get_backend()
            is_valid, error_msg = backend.validate_config()
            if is_valid:
                console.print(f"[bold green]✓[/bold green] Backend connection validated successfully")
            else:
                console.print(f"[bold yellow]⚠[/bold yellow] Backend validation failed: {error_msg}")
        except Exception as e:
            console.print(f"[bold yellow]⚠[/bold yellow] Could not validate backend: {e}")
    else:
        console.print(
            "[bold yellow]CLI is not fully configured.[/bold yellow] "
            "Run 'boring setup' to complete configuration."
        )

    console.print(f"\n[dim]Config file: {config.CONFIG_FILE}[/dim]")
