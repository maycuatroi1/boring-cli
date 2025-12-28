"""Boring CLI - Manage Lark Suite tasks from the command line."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("boring-cli")
except PackageNotFoundError:
    __version__ = "0.0.0"  # Development mode
