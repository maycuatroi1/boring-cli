"""Setup command for Boring CLI."""

import webbrowser

import click
from rich.console import Console

from .. import config
from ..client import APIClient

console = Console()


@click.command()
@click.option(
    "--server-url",
    prompt="Server URL",
    default=lambda: config.get_server_url() or "https://boring.omelet.tech/api",
    help="URL of the Boring Agents API server",
)
def setup(server_url: str):
    """Configure the CLI and login to Lark."""
    console.print("\n[bold blue]Configuring Boring CLI...[/bold blue]")
    console.print(f"Server URL: [cyan]{server_url}[/cyan]")

    config.set_server_url(server_url)

    bugs_dir = click.prompt(
        "Bugs output directory", default=config.get_bugs_dir() or "/tmp/bugs"
    )
    config.set_bugs_dir(bugs_dir)

    tasklist_guid = click.prompt(
        "Tasklist GUID (from Lark)", default=config.get_tasklist_guid() or ""
    )
    if tasklist_guid:
        config.set_tasklist_guid(tasklist_guid)

    section_guid = click.prompt(
        "In-progress Section GUID", default=config.get_section_guid() or ""
    )
    if section_guid:
        config.set_section_guid(section_guid)

    solved_section_guid = click.prompt(
        "Solved Section GUID", default=config.get_solved_section_guid() or ""
    )
    if solved_section_guid:
        config.set_solved_section_guid(solved_section_guid)

    console.print("\n[bold]Starting Lark OAuth login...[/bold]")

    client = APIClient()
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

    if jwt_token:
        config.set_jwt_token(jwt_token.strip())
        console.print("\n[bold green]Login successful![/bold green]")
        console.print(f"Configuration saved to: [dim]{config.CONFIG_FILE}[/dim]")
        console.print(
            "\n[bold green]Setup complete![/bold green] You can now use 'boring download' and 'boring solve'."
        )
    else:
        console.print("\n[bold red]No token provided.[/bold red]")
        raise click.Abort()
