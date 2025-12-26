"""Configuration management for Boring CLI."""

import os
from pathlib import Path
from typing import Optional

import yaml

CONFIG_DIR = Path.home() / ".boring-agents"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_value(key: str) -> Optional[str]:
    """Get a configuration value."""
    return load_config().get(key)


def set_value(key: str, value: str) -> None:
    """Set a configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)


# Convenience accessors
def get_server_url() -> Optional[str]:
    return get_value("server_url")


def get_jwt_token() -> Optional[str]:
    return get_value("jwt_token")


def get_bugs_dir() -> Optional[str]:
    return get_value("bugs_dir")


def get_tasklist_guid() -> Optional[str]:
    return get_value("tasklist_guid")


def get_section_guid() -> Optional[str]:
    return get_value("section_guid")


def get_solved_section_guid() -> Optional[str]:
    return get_value("solved_section_guid")


def set_server_url(url: str) -> None:
    set_value("server_url", url)


def set_jwt_token(token: str) -> None:
    set_value("jwt_token", token)


def set_bugs_dir(path: str) -> None:
    set_value("bugs_dir", path)


def set_tasklist_guid(guid: str) -> None:
    set_value("tasklist_guid", guid)


def set_section_guid(guid: str) -> None:
    set_value("section_guid", guid)


def set_solved_section_guid(guid: str) -> None:
    set_value("solved_section_guid", guid)


def is_configured() -> bool:
    """Check if the CLI is properly configured."""
    config = load_config()
    return all([config.get("server_url"), config.get("jwt_token"), config.get("bugs_dir")])
