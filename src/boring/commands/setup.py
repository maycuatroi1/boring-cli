"""Setup command for Boring CLI."""

import webbrowser

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from .. import config
from ..backends import LarkBackend, KanbanBackend

console = Console()


def setup_lark():
    """Setup Lark backend with auto-discovery."""
    from ..client import APIClient

    console.print("\n[bold cyan]Lark Suite Setup[/bold cyan]")

    # Server URL
    server_url = click.prompt(
        "Server URL", default=config.get_server_url() or "https://boring.omelet.tech/api"
    )
    config.set_server_url(server_url)

    # Bugs directory
    bugs_dir = click.prompt(
        "Bugs output directory", default=config.get_bugs_dir() or "/tmp/bugs"
    )
    config.set_bugs_dir(bugs_dir)

    # OAuth flow
    console.print("\n[bold]Starting Lark OAuth login...[/bold]")
    client = APIClient(base_url=server_url)

    try:
        auth_url = client.get_login_url()
        console.print("\n[yellow]Opening browser for Lark login...[/yellow]")
        console.print(f"If browser doesn't open, visit:\n[link]{auth_url}[/link]")
        webbrowser.open(auth_url)
    except Exception as e:
        console.print(f"\n[red]Could not get auth URL: {e}[/red]")
        raise click.Abort()

    console.print("\n[dim]After login, you'll see a JSON response with your token.[/dim]")
    console.print("[dim]Copy the 'access_token' value from the response.[/dim]\n")

    jwt_token = click.prompt("Paste your access_token here")

    if not jwt_token:
        console.print("\n[bold red]No token provided.[/bold red]")
        raise click.Abort()

    config.set_jwt_token(jwt_token.strip())

    # Get Lark token
    console.print("\n[bold]Fetching Lark token...[/bold]")
    try:
        client = APIClient(base_url=server_url, token=jwt_token.strip())
        lark_token_data = client.get_lark_token()
        lark_token = lark_token_data.get("access_token")
        config.set_lark_token(lark_token)
    except Exception as e:
        console.print(f"[red]Failed to get Lark token: {e}[/red]")
        raise click.Abort()

    # Auto-discover tasklists
    console.print("\n[bold]Discovering tasklists...[/bold]")
    backend = LarkBackend(
        server_url=server_url, jwt_token=jwt_token.strip(), lark_token=lark_token
    )

    try:
        boards = backend.list_boards()
    except Exception as e:
        console.print(f"[red]Failed to list tasklists: {e}[/red]")
        raise click.Abort()

    if not boards:
        console.print("[yellow]No tasklists found.[/yellow]")
        raise click.Abort()

    # Display tasklists
    table = Table(title="Available Tasklists")
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("ID", style="dim")

    for idx, board in enumerate(boards, 1):
        table.add_row(str(idx), board.name, board.id)

    console.print()
    console.print(table)

    # Select tasklist
    while True:
        selection = Prompt.ask("\nSelect a tasklist", default="1")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(boards):
                selected_board = boards[idx]
                config.set_tasklist_guid(selected_board.id)
                console.print(f"[green]Selected:[/green] {selected_board.name}")
                break
            else:
                console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")

    # Auto-discover sections
    console.print("\n[bold]Discovering sections...[/bold]")
    try:
        sections = backend.list_sections(selected_board.id)
    except Exception as e:
        console.print(f"[red]Failed to list sections: {e}[/red]")
        raise click.Abort()

    if not sections:
        console.print("[yellow]No sections found.[/yellow]")
        raise click.Abort()

    # Display sections
    table = Table(title="Available Sections")
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("ID", style="dim")

    for idx, section in enumerate(sections, 1):
        table.add_row(str(idx), section.name, section.id)

    console.print()
    console.print(table)

    # Select in-progress section
    while True:
        selection = Prompt.ask("\nSelect In-Progress section", default="1")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(sections):
                selected_section = sections[idx]
                config.set_section_guid(selected_section.id)
                console.print(f"[green]In-Progress:[/green] {selected_section.name}")
                break
            else:
                console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")

    # Select solved section
    while True:
        selection = Prompt.ask("Select Solved/Done section", default="2")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(sections):
                solved_section = sections[idx]
                config.set_solved_section_guid(solved_section.id)
                console.print(f"[green]Solved:[/green] {solved_section.name}")
                break
            else:
                console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")


def setup_kanban():
    """Setup Kanban backend with auto-discovery."""
    console.print("\n[bold cyan]Kanban (Outline) Setup[/bold cyan]")

    # Server URL (Common for all backends)
    server_url = click.prompt(
        "Server URL", default=config.get_server_url() or "https://boring.omelet.tech/api"
    )
    config.set_server_url(server_url)

    # Bugs directory
    bugs_dir = click.prompt(
        "Bugs output directory", default=config.get_bugs_dir() or "/tmp/bugs"
    )
    config.set_bugs_dir(bugs_dir)

    # Kanban base URL
    kanban_base_url = click.prompt(
        "Kanban Base URL",
        default=config.get_kanban_base_url() or "https://local.outline.dev:3000",
    )
    config.set_kanban_base_url(kanban_base_url)

    # Kanban API key
    kanban_api_key = click.prompt(
        "Kanban API Key", default=config.get_kanban_api_key() or ""
    )
    if not kanban_api_key:
        console.print("\n[bold red]No API key provided.[/bold red]")
        raise click.Abort()
    config.set_kanban_api_key(kanban_api_key.strip())

    # Validate connection
    console.print("\n[bold]Validating connection...[/bold]")
    backend = KanbanBackend(base_url=kanban_base_url, api_key=kanban_api_key.strip())

    is_valid, error_msg = backend.validate_config()
    if not is_valid:
        console.print(f"[red]Connection failed: {error_msg}[/red]")
        raise click.Abort()

    console.print("[green]Connection successful![/green]")

    # Auto-discover boards
    console.print("\n[bold]Discovering boards...[/bold]")
    try:
        boards = backend.list_boards()
    except Exception as e:
        console.print(f"[red]Failed to list boards: {e}[/red]")
        raise click.Abort()

    if not boards:
        console.print("[yellow]No boards found.[/yellow]")
        raise click.Abort()

    # Display boards
    table = Table(title="Available Boards")
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("ID", style="dim")

    for idx, board in enumerate(boards, 1):
        table.add_row(str(idx), board.name, board.id)

    console.print()
    console.print(table)

    # Select board
    while True:
        selection = Prompt.ask("\nSelect a board", default="1")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(boards):
                selected_board = boards[idx]
                config.set_kanban_board_id(selected_board.id)
                console.print(f"[green]Selected:[/green] {selected_board.name}")
                break
            else:
                console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")

    # Auto-discover columns
    console.print("\n[bold]Discovering columns...[/bold]")
    try:
        sections = backend.list_sections(selected_board.id)
    except Exception as e:
        console.print(f"[red]Failed to list columns: {e}[/red]")
        raise click.Abort()

    if not sections:
        console.print("[yellow]No columns found.[/yellow]")
        raise click.Abort()

    # Display columns
    table = Table(title="Available Columns")
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("ID", style="dim")

    for idx, section in enumerate(sections, 1):
        table.add_row(str(idx), section.name, section.id)

    console.print()
    console.print(table)

    # Select in-progress column
    while True:
        selection = Prompt.ask("\nSelect In-Progress column", default="1")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(sections):
                selected_section = sections[idx]
                config.set_kanban_list_id(selected_section.id)
                console.print(f"[green]In-Progress:[/green] {selected_section.name}")
                break
            else:
                console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")

    # Select done column
    while True:
        selection = Prompt.ask("Select Done/Solved column", default="2")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(sections):
                done_section = sections[idx]
                config.set_kanban_done_list_id(done_section.id)
                console.print(f"[green]Done:[/green] {done_section.name}")
                break
            else:
                console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")


@click.command()
def setup():
    """Configure the CLI with Lark or Kanban backend."""
    console.print("\n[bold blue]Boring CLI Setup[/bold blue]")
    console.print("\nSelect task management backend:")
    console.print("  [cyan]1.[/cyan] Lark Suite")
    console.print("  [cyan]2.[/cyan] Kanban (Outline)")

    current_backend = config.get_backend_type()
    default_choice = "1" if current_backend == "lark" else "2"

    while True:
        choice = Prompt.ask("\nSelect backend", choices=["1", "2"], default=default_choice)

        if choice == "1":
            config.set_backend_type("lark")
            try:
                setup_lark()
                break
            except click.Abort:
                console.print("\n[yellow]Setup cancelled.[/yellow]")
                raise
            except Exception as e:
                console.print(f"\n[red]Setup failed: {e}[/red]")
                raise click.Abort()

        elif choice == "2":
            config.set_backend_type("kanban")
            try:
                setup_kanban()
                break
            except click.Abort:
                console.print("\n[yellow]Setup cancelled.[/yellow]")
                raise
            except Exception as e:
                console.print(f"\n[red]Setup failed: {e}[/red]")
                raise click.Abort()

    console.print("\n[bold green]✓ Setup complete![/bold green]")
    console.print(f"Configuration saved to: [dim]{config.CONFIG_FILE}[/dim]")
    console.print(
        "\nYou can now use:"
        "\n  [cyan]boring sections[/cyan] - List boards and sections"
        "\n  [cyan]boring download[/cyan] - Download tasks/cards"
        "\n  [cyan]boring solve[/cyan] - Move completed items to done"
        "\n  [cyan]boring status[/cyan] - Show configuration"
    )
