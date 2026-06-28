from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntegrationMessage:
    level: str  # info | warning | error
    text: str
    code: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "text": self.text, "code": self.code}


@dataclass
class GitHubSyncResult:
    attempted: bool = False
    success: bool = False
    mode: str = "DISABLED"  # DISABLED | STUB | REAL | FAILED
    http_status: int | None = None
    issue_number: int | None = None
    issue_url: str | None = None
    error: str = ""
    response_body: str = ""
    messages: list[IntegrationMessage] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "attempted": self.attempted,
            "success": self.success,
            "mode": self.mode,
            "http_status": self.http_status,
            "issue_number": self.issue_number,
            "issue_url": self.issue_url,
            "error": self.error,
            "messages": [m.as_dict() for m in self.messages],
        }


def parse_github_error(response) -> str:
    try:
        payload = response.json()
    except Exception:
        return response.text[:500] or f"HTTP {response.status_code}"
    if isinstance(payload, dict):
        if payload.get("message"):
            details = payload.get("errors")
            if details:
                return f"{payload['message']}: {details}"
            return str(payload["message"])
    return response.text[:500] or f"HTTP {response.status_code}"


def github_issue_create_hint(status_code: int, repo: str) -> str:
    if status_code != 404:
        return ""
    return (
        f"GitHub returned 404 for POST /repos/{repo}/issues. "
        "The token can often read the repo but is missing permission to create issues. "
        "Fix: GitHub → Settings → Developer settings → Personal access tokens → edit your token → "
        "Repository access: select this repo → Permissions → Issues: Read and write. "
        "For classic tokens, enable the full 'repo' scope. Then update GITHUB_TOKEN in backend/.env and restart Django."
    )
