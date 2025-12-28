"""Version check for Boring CLI."""

import json
from typing import Optional, Tuple

import httpx
from packaging import version as pkg_version

from . import __version__

PYPI_URL = "https://pypi.org/pypi/boring-cli/json"


def get_latest_version() -> Optional[str]:
    """Fetch the latest version from PyPI."""
    try:
        with httpx.Client(timeout=3) as client:
            response = client.get(PYPI_URL)
            response.raise_for_status()
            data = response.json()
            return data.get("info", {}).get("version")
    except Exception:
        return None


def check_for_updates() -> Tuple[bool, Optional[str], str]:
    """
    Check if a newer version is available.

    Returns:
        Tuple of (update_available, latest_version, current_version)
    """
    current = __version__
    latest = get_latest_version()

    if latest is None:
        return False, None, current

    try:
        update_available = pkg_version.parse(latest) > pkg_version.parse(current)
        return update_available, latest, current
    except Exception:
        return False, latest, current
