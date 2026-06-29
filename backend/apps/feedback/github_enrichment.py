"""GitHub issue post-create enrichment: milestone, labels, project, branch."""

from __future__ import annotations

import logging
import re
from typing import Any

import requests

from apps.feedback.github_sync import IntegrationMessage

logger = logging.getLogger(__name__)


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


DEFAULT_BRANCH_NAME_TEMPLATE = "#{issue}-{feedback_number}-{gurukulam_id}-{slug}"
MAX_BRANCH_NAME_LEN = 200


def sanitize_branch_segment(value: str) -> str:
    segment = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip())
    return segment.strip("-") or "na"


def build_issue_branch_name(
    *,
    issue_number: int,
    feedback_number: str,
    gurukulam_id: str,
    title: str,
    branch_prefix: str = "",
    template: str = DEFAULT_BRANCH_NAME_TEMPLATE,
    max_len: int = MAX_BRANCH_NAME_LEN,
) -> str:
    fb_number = sanitize_branch_segment(feedback_number)
    gurukulam = sanitize_branch_segment(gurukulam_id)
    branch_template = template or DEFAULT_BRANCH_NAME_TEMPLATE
    fixed = branch_template.format(
        issue=issue_number,
        feedback_number=fb_number,
        gurukulam_id=gurukulam,
        slug="",
    ).rstrip("-")
    prefix = f"{branch_prefix}{fixed}-"
    slug_len = max(8, max_len - len(prefix))
    slug = slugify_branch(title, max_len=slug_len)
    return f"{prefix}{slug}"[:max_len]


def slugify_branch(text: str, max_len: int = 48) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (slug[:max_len] if slug else "issue")


def resolve_milestone_number(api_url: str, repo: str, token: str, milestone: str) -> int | None:
    if not milestone:
        return None
    if milestone.isdigit():
        return int(milestone)
    headers = _headers(token)
    response = requests.get(
        f"{api_url}/repos/{repo}/milestones",
        headers=headers,
        params={"state": "open", "per_page": 100},
        timeout=20,
    )
    if response.status_code != 200:
        return None
    target = milestone.strip().lower()
    for item in response.json():
        if str(item.get("title", "")).lower() == target:
            return item.get("number")
    return None


def get_default_branch(api_url: str, repo: str, token: str, configured: str = "") -> str:
    if configured:
        return configured
    response = requests.get(f"{api_url}/repos/{repo}", headers=_headers(token), timeout=20)
    if response.status_code == 200:
        return response.json().get("default_branch", "main")
    return "main"


def create_issue_branch(
    api_url: str,
    repo: str,
    token: str,
    issue_number: int,
    feedback_title: str,
    *,
    feedback_number: str,
    gurukulam_id: str,
    default_branch: str = "",
    branch_prefix: str = "",
    branch_name_template: str = DEFAULT_BRANCH_NAME_TEMPLATE,
) -> tuple[str | None, list[IntegrationMessage]]:
    messages: list[IntegrationMessage] = []
    base = get_default_branch(api_url, repo, token, default_branch)
    headers = _headers(token)
    ref_resp = requests.get(f"{api_url}/repos/{repo}/git/ref/heads/{base}", headers=headers, timeout=20)
    if ref_resp.status_code != 200:
        messages.append(IntegrationMessage(
            level="warning",
            code="github_branch_base_failed",
            text=f"Could not resolve base branch '{base}' (HTTP {ref_resp.status_code}). Branch not created.",
        ))
        return None, messages

    sha = ref_resp.json()["object"]["sha"]
    branch_name = build_issue_branch_name(
        issue_number=issue_number,
        feedback_number=feedback_number,
        gurukulam_id=gurukulam_id,
        title=feedback_title,
        branch_prefix=branch_prefix,
        template=branch_name_template,
    )
    create_resp = requests.post(
        f"{api_url}/repos/{repo}/git/refs",
        headers=headers,
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        timeout=20,
    )
    if create_resp.status_code == 201:
        messages.append(IntegrationMessage(
            level="info",
            code="github_branch_created",
            text=f"Created branch '{branch_name}' from '{base}'.",
        ))
        return branch_name, messages

    if create_resp.status_code == 422 and "Reference already exists" in create_resp.text:
        messages.append(IntegrationMessage(
            level="warning",
            code="github_branch_exists",
            text=f"Branch '{branch_name}' already exists.",
        ))
        return branch_name, messages

    messages.append(IntegrationMessage(
        level="warning",
        code="github_branch_failed",
        text=f"Branch creation failed (HTTP {create_resp.status_code}).",
    ))
    return None, messages


def add_issue_to_project_v2(token: str, project_node_id: str, issue_node_id: str) -> list[IntegrationMessage]:
    if not project_node_id or not issue_node_id:
        return []
    query = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item { id }
      }
    }
    """
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": query, "variables": {"projectId": project_node_id, "contentId": issue_node_id}},
        timeout=20,
    )
    if response.status_code == 200 and not response.json().get("errors"):
        return [IntegrationMessage(
            level="info",
            code="github_project_linked",
            text="Issue added to GitHub Project.",
        )]
    logger.warning("GitHub project link failed: %s", response.text[:300])
    return [IntegrationMessage(
        level="warning",
        code="github_project_failed",
        text="Could not add issue to GitHub Project. Check GITHUB_PROJECT_NODE_ID and token project permissions.",
    )]


def enrich_created_issue(
    cfg: dict[str, Any],
    *,
    api_url: str,
    repo: str,
    token: str,
    issue_data: dict[str, Any],
    feedback_title: str,
    feedback_number: str,
    gurukulam_id: str,
) -> tuple[dict[str, Any], list[IntegrationMessage]]:
    """Apply milestone (already on issue), project link, and branch creation."""
    messages: list[IntegrationMessage] = []
    metadata: dict[str, Any] = {
        "branch_name": "",
        "milestone": cfg.get("milestone", ""),
        "project_node_id": cfg.get("project_node_id", ""),
    }

    if cfg.get("project_node_id") and issue_data.get("node_id"):
        messages.extend(add_issue_to_project_v2(token, cfg["project_node_id"], issue_data["node_id"]))

    if cfg.get("auto_create_branch", True):
        branch_name, branch_messages = create_issue_branch(
            api_url,
            repo,
            token,
            issue_data["number"],
            feedback_title,
            feedback_number=feedback_number,
            gurukulam_id=gurukulam_id,
            default_branch=cfg.get("default_branch", ""),
            branch_prefix=cfg.get("branch_prefix", ""),
            branch_name_template=cfg.get("branch_name_template", DEFAULT_BRANCH_NAME_TEMPLATE),
        )
        messages.extend(branch_messages)
        metadata["branch_name"] = branch_name or ""

    return metadata, messages


def build_issue_create_payload(
    cfg: dict[str, Any],
    *,
    api_url: str,
    repo: str,
    token: str,
    title: str,
    body: str,
    labels: list[str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    # assignees intentionally omitted — manual in GitHub UI
    milestone = resolve_milestone_number(api_url, repo, token, cfg.get("milestone", ""))
    if milestone:
        payload["milestone"] = milestone
    return payload
