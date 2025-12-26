"""Sections command for Boring CLI."""

import click
from rich.console import Console
from rich.table import Table

from .. import config
from ..client import APIClient, LarkClient

console = Console()


@click.command()
def sections():
    """List all tasklists and sections from Lark."""
    if not config.is_configured():
        console.print("[bold red]CLI not configured.[/bold red] Run 'boring setup' first.")
        raise click.Abort()

    console.print("[bold]Fetching Lark token...[/bold]")

    api_client = APIClient()
    try:
        lark_token_data = api_client.get_lark_token()
        lark_access_token = lark_token_data.get("access_token")
        config.set_lark_token(lark_access_token)
    except Exception as e:
        console.print(f"[bold red]Failed to get Lark token:[/bold red] {e}")
        raise click.Abort()

    console.print("[bold]Fetching tasklists...[/bold]\n")

    lark_client = LarkClient(access_token=lark_access_token)

    try:
        tasklists_response = lark_client.list_tasklists()
        if tasklists_response.get("code") != 0:
            console.print(f"[bold red]Failed to list tasklists:[/bold red] {tasklists_response.get('msg')}")
            raise click.Abort()

        tasklists = tasklists_response.get("data", {}).get("items", [])

        if not tasklists:
            console.print("[yellow]No tasklists found.[/yellow]")
            return

        for tasklist in tasklists:
            tasklist_guid = tasklist.get("guid")
            tasklist_name = tasklist.get("name", "Unnamed")

            console.print(f"[bold cyan]Tasklist:[/bold cyan] {tasklist_name}")
            console.print(f"[dim]GUID: {tasklist_guid}[/dim]\n")

            try:
                sections_response = lark_client.list_sections(tasklist_guid)
                if sections_response.get("code") != 0:
                    console.print(f"  [yellow]Could not fetch sections: {sections_response.get('msg')}[/yellow]")
                    continue

                sections_list = sections_response.get("data", {}).get("items", [])

                if not sections_list:
                    console.print("  [dim]No sections[/dim]\n")
                    continue

                table = Table(show_header=True, header_style="bold")
                table.add_column("Section Name", style="green")
                table.add_column("GUID", style="dim")

                for section in sections_list:
                    section_name = section.get("name", "Unnamed")
                    section_guid = section.get("guid", "")
                    table.add_row(section_name, section_guid)

                console.print(table)
                console.print()

            except Exception as e:
                console.print(f"  [yellow]Error fetching sections: {e}[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Failed to fetch tasklists:[/bold red] {e}")
        raise click.Abort()
