"""Sync Claude configuration from server."""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..client import APIClient
from ..config import get_value

console = Console()


def get_git_repo_name() -> Optional[str]:
    """Get repository name from git remote URL."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        # Extract repo name from URL
        # Handle both HTTPS and SSH URLs
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]

        # Handle SSH format: git@github.com:user/repo
        if ":" in remote_url and "@" in remote_url:
            repo_name = remote_url.split(":")[-1].split("/")[-1]
        else:
            # Handle HTTPS format: https://github.com/user/repo
            repo_name = remote_url.split("/")[-1]

        return repo_name
    except subprocess.CalledProcessError:
        return None


def get_git_root() -> Optional[Path]:
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


@click.command()
@click.option("--repo", "-r", help="Repository name (auto-detected from git if not provided)")
@click.option("--machine", "-m", help="Machine name for variable substitution")
@click.option("--dry-run", is_flag=True, help="Show what would be synced without making changes")
def sync(repo: Optional[str], machine: Optional[str], dry_run: bool):
    """Sync Claude configuration from server to local .claude directory.

    Auto-detects the repository name from git remote URL.
    Use machine name for path variable substitution.

    \b
    Examples:
      boring sync                    # Auto-detect repo
      boring sync -r my-repo         # Specify repo name
      boring sync -m macbook-pro     # Use machine-specific paths
      boring sync --dry-run          # Preview changes
    """
    # Auto-detect repo name
    if not repo:
        repo = get_git_repo_name()
        if not repo:
            console.print("[red]Error:[/red] Could not detect repository name.")
            console.print("Make sure you're in a git repository or specify --repo")
            raise click.Abort()

    # Get git root for .claude directory
    git_root = get_git_root()
    if not git_root:
        console.print("[red]Error:[/red] Not in a git repository.")
        raise click.Abort()

    console.print(f"[cyan]Syncing configuration for:[/cyan] {repo}")
    if machine:
        console.print(f"[cyan]Using machine:[/cyan] {machine}")

    # Fetch config from server
    try:
        client = APIClient()
        config = client.sync_claude_config(repo, machine)
    except Exception as e:
        console.print(f"[red]Error fetching config:[/red] {e}")
        raise click.Abort()

    claude_dir = git_root / ".claude"

    if dry_run:
        console.print("\n[yellow]Dry run - would create/update:[/yellow]")
        _show_dry_run(config, claude_dir)
        return

    # Create .claude directory structure
    _sync_config(config, claude_dir)

    console.print("\n[green]✓ Sync complete![/green]")


def _show_dry_run(config: dict, claude_dir: Path):
    """Show what would be synced."""
    if config.get("claude_md"):
        console.print(f"  • {claude_dir / 'CLAUDE.md'}")

    if config.get("settings_json"):
        console.print(f"  • {claude_dir / 'settings.local.json'}")

    if config.get("mcp_json", {}).get("mcpServers"):
        console.print(f"  • {claude_dir.parent / '.mcp.json'}")

    for agent in config.get("agents", []):
        console.print(f"  • {claude_dir / 'agents' / f'{agent['name']}.md'}")

    for skill in config.get("skills", []):
        console.print(f"  • {claude_dir / 'skills' / skill['name'] / 'SKILL.md'}")
        for script in skill.get("scripts", []):
            console.print(f"    • {claude_dir / 'skills' / skill['name'] / 'scripts' / script['filename']}")

    for command in config.get("commands", []):
        console.print(f"  • {claude_dir / 'commands' / f'{command['name']}.md'}")


def _sync_config(config: dict, claude_dir: Path):
    """Write configuration files to disk."""
    # Create directories
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / "agents").mkdir(exist_ok=True)
    (claude_dir / "skills").mkdir(exist_ok=True)
    (claude_dir / "commands").mkdir(exist_ok=True)

    # Write CLAUDE.md
    if config.get("claude_md"):
        claude_md_path = claude_dir / "CLAUDE.md"
        claude_md_path.write_text(config["claude_md"])
        console.print(f"  [green]✓[/green] CLAUDE.md")

    # Write settings.local.json
    if config.get("settings_json"):
        settings_path = claude_dir / "settings.local.json"
        settings_path.write_text(json.dumps(config["settings_json"], indent=2) + "\n")
        console.print(f"  [green]✓[/green] settings.local.json")

    # Write .mcp.json (in repo root, not .claude)
    if config.get("mcp_json", {}).get("mcpServers"):
        mcp_path = claude_dir.parent / ".mcp.json"
        mcp_path.write_text(json.dumps(config["mcp_json"], indent=2) + "\n")
        console.print(f"  [green]✓[/green] .mcp.json")

    # Write agents
    for agent in config.get("agents", []):
        agent_path = claude_dir / "agents" / f"{agent['name']}.md"
        agent_path.write_text(agent["content"])
        console.print(f"  [green]✓[/green] agents/{agent['name']}.md")

    # Write skills
    for skill in config.get("skills", []):
        skill_dir = claude_dir / "skills" / skill["name"]
        skill_dir.mkdir(exist_ok=True)

        skill_md_path = skill_dir / "SKILL.md"
        skill_md_path.write_text(skill["skill_md"])
        console.print(f"  [green]✓[/green] skills/{skill['name']}/SKILL.md")

        # Write scripts
        if skill.get("scripts"):
            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)

            for script in skill["scripts"]:
                script_path = scripts_dir / script["filename"]
                script_path.write_text(script["content"])

                # Make executable if needed
                if script.get("is_executable"):
                    os.chmod(script_path, 0o755)

                console.print(f"    [green]✓[/green] scripts/{script['filename']}")

    # Write commands
    for command in config.get("commands", []):
        command_path = claude_dir / "commands" / f"{command['name']}.md"
        command_path.write_text(command["content"])
        console.print(f"  [green]✓[/green] commands/{command['name']}.md")
