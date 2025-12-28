"""HTTP client for Boring Agents API."""

from typing import Optional

import httpx

from .config import get_jwt_token, get_server_url, get_lark_token

LARK_BASE_URL = "https://open.larksuite.com/open-apis"


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
            response = client.get(f"{self.base_url}/v1/auth/login")
            response.raise_for_status()
            return response.json().get("auth_url")

    def complete_login(self, code: str) -> dict:
        """Complete the OAuth login with the authorization code."""
        if not self.base_url:
            raise Exception("Server URL not configured.")
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/v1/auth/callback", params={"code": code}
            )
            response.raise_for_status()
            return response.json()

    def get_me(self) -> dict:
        """Get current user information."""
        self._check_config()
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/v1/auth/me", headers=self._headers()
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
                f"{self.base_url}/v1/tasks/",
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
                f"{self.base_url}/v1/tasks/critical", headers=self._headers()
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
                f"{self.base_url}/v1/tasks/download",
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
                f"{self.base_url}/v1/tasks/{task_guid}/solve",
                headers=self._headers(),
                json={"tasklist_guid": tasklist_guid, "section_guid": section_guid},
            )
            response.raise_for_status()
            return response.json()

    def get_lark_token(self) -> dict:
        """Get Lark access token from server."""
        self._check_config()
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/v1/auth/lark-token",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()


class LarkClient:
    """Client for direct Lark API calls."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or get_lark_token()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _check_token(self) -> None:
        if not self.access_token:
            raise Exception("Lark token not available. Run 'boring setup' first.")

    def list_tasklists(self, page_size: int = 50) -> dict:
        """List all tasklists."""
        self._check_token()
        with httpx.Client() as client:
            response = client.get(
                f"{LARK_BASE_URL}/task/v2/tasklists",
                headers=self._headers(),
                params={"page_size": page_size},
            )
            response.raise_for_status()
            return response.json()

    def get_tasklist(self, tasklist_guid: str) -> dict:
        """Get tasklist details including sections."""
        self._check_token()
        with httpx.Client() as client:
            response = client.get(
                f"{LARK_BASE_URL}/task/v2/tasklists/{tasklist_guid}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    def list_sections(self, tasklist_guid: str, page_size: int = 50) -> dict:
        """List all sections in a tasklist."""
        self._check_token()
        with httpx.Client() as client:
            response = client.get(
                f"{LARK_BASE_URL}/task/v2/sections",
                headers=self._headers(),
                params={
                    "resource_type": "tasklist",
                    "resource_id": tasklist_guid,
                    "page_size": page_size,
                },
            )
            response.raise_for_status()
            return response.json()

    def list_tasks_in_section(self, section_guid: str, page_size: int = 50) -> dict:
        """List all tasks in a section."""
        self._check_token()
        with httpx.Client() as client:
            response = client.get(
                f"{LARK_BASE_URL}/task/v2/sections/{section_guid}/tasks",
                headers=self._headers(),
                params={"page_size": page_size},
            )
            response.raise_for_status()
            return response.json()

    def get_task(self, task_guid: str) -> dict:
        self._check_token()
        with httpx.Client(timeout=60) as client:
            response = client.get(
                f"{LARK_BASE_URL}/task/v2/tasks/{task_guid}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    def list_task_comments(self, task_guid: str, page_size: int = 50) -> list:
        self._check_token()
        all_comments = []
        page_token = None
        with httpx.Client(timeout=60) as client:
            while True:
                params = {
                    "resource_type": "task",
                    "resource_id": task_guid,
                    "page_size": page_size,
                }
                if page_token:
                    params["page_token"] = page_token
                response = client.get(
                    f"{LARK_BASE_URL}/task/v2/comments",
                    headers=self._headers(),
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("code") != 0:
                    break
                items = data.get("data", {}).get("items", [])
                all_comments.extend(items)
                page_token = data.get("data", {}).get("page_token")
                if not page_token or not data.get("data", {}).get("has_more", False):
                    break
        return all_comments
