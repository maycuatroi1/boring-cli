"""HTTP client for Boring Agents API."""

from typing import Optional

import httpx

from .config import get_jwt_token, get_server_url


class APIClient:
    """Client for interacting with the Boring Agents API."""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or get_server_url()
        self.token = token or get_jwt_token()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _check_config(self) -> None:
        if not self.base_url:
            raise Exception("Server URL not configured. Run 'boring setup' first.")
        if not self.token:
            raise Exception("Not logged in. Run 'boring setup' first.")

    def get_login_url(self) -> str:
        """Get the Lark OAuth login URL."""
        if not self.base_url:
            raise Exception("Server URL not configured.")
        with httpx.Client() as client:
            response = client.get(f"{self.base_url}/api/v1/auth/login")
            response.raise_for_status()
            return response.json().get("auth_url")

    def complete_login(self, code: str) -> dict:
        """Complete the OAuth login with the authorization code."""
        if not self.base_url:
            raise Exception("Server URL not configured.")
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/v1/auth/callback", params={"code": code}
            )
            response.raise_for_status()
            return response.json()

    def get_me(self) -> dict:
        """Get current user information."""
        self._check_config()
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/v1/auth/me", headers=self._headers()
            )
            response.raise_for_status()
            return response.json()

    def get_tasks(
        self, labels: Optional[str] = None, section_guid: Optional[str] = None
    ) -> dict:
        """Get tasks with optional filters."""
        self._check_config()
        params = {}
        if labels:
            params["labels"] = labels
        if section_guid:
            params["section_guid"] = section_guid

        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/v1/tasks/",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            return response.json()

    def get_critical_tasks(self) -> dict:
        """Get critical and blocked tasks."""
        self._check_config()
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/v1/tasks/critical", headers=self._headers()
            )
            response.raise_for_status()
            return response.json()

    def download_tasks(
        self, labels: Optional[str] = None, section_guid: Optional[str] = None
    ) -> dict:
        """Download tasks as markdown content."""
        self._check_config()
        params = {}
        if labels:
            params["labels"] = labels
        if section_guid:
            params["section_guid"] = section_guid

        with httpx.Client(timeout=120) as client:
            response = client.get(
                f"{self.base_url}/api/v1/tasks/download",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            return response.json()

    def solve_task(
        self, task_guid: str, tasklist_guid: str, section_guid: str
    ) -> dict:
        """Move a task to the solved section."""
        self._check_config()
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/api/v1/tasks/{task_guid}/solve",
                headers=self._headers(),
                json={"tasklist_guid": tasklist_guid, "section_guid": section_guid},
            )
            response.raise_for_status()
            return response.json()
