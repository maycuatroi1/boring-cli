"""Main entry point for Boring CLI."""

import click

from . import __version__
from .commands.download import download
from .commands.setup import setup
from .commands.solve import solve
from .commands.status import status


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
    """
    pass


cli.add_command(setup)
cli.add_command(download)
cli.add_command(solve)
cli.add_command(status)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
