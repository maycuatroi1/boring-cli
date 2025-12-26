"""Setup command for Boring CLI."""

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import click
from rich.console import Console

from .. import config
from ..client import APIClient

console = Console()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler for OAuth callback."""

    code = None

    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        if "code" in params:
            OAuthCallbackHandler.code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #10B981;">Login Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """
            )
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code parameter")

    def log_message(self, format, *args):
        pass


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

    server = HTTPServer(("localhost", 9876), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.start()

    client = APIClient()
    try:
        auth_url = client.get_login_url()
        full_auth_url = auth_url + "&redirect_uri=http://localhost:9876/callback"
        console.print("\n[yellow]Opening browser for Lark login...[/yellow]")
        console.print(f"If browser doesn't open, visit: [link]{full_auth_url}[/link]")
        webbrowser.open(full_auth_url)
    except Exception as e:
        console.print(f"\n[yellow]Note: Could not get auth URL from server: {e}[/yellow]")
        console.print("Please complete OAuth flow manually and get the code.")
        code = click.prompt("Enter the OAuth code")
        OAuthCallbackHandler.code = code

    if not OAuthCallbackHandler.code:
        console.print("[dim]Waiting for OAuth callback...[/dim]")
        server_thread.join(timeout=300)

    if OAuthCallbackHandler.code:
        try:
            result = client.complete_login(OAuthCallbackHandler.code)
            token = result.get("token", {}).get("access_token")
            user = result.get("user", {})

            config.set_jwt_token(token)

            console.print("\n[bold green]Login successful![/bold green]")
            console.print(
                f"Logged in as: [cyan]{user.get('name') or user.get('email') or 'User'}[/cyan]"
            )
            console.print(f"\nConfiguration saved to: [dim]{config.CONFIG_FILE}[/dim]")
        except Exception as e:
            console.print(f"\n[bold red]Login failed: {e}[/bold red]")
            raise click.Abort()
    else:
        console.print("\n[bold red]OAuth flow timed out or failed.[/bold red]")
        raise click.Abort()

    server.server_close()
    console.print(
        "\n[bold green]Setup complete![/bold green] You can now use 'boring download' and 'boring solve'."
    )
