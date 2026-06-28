"""Issue tracker and Slack integrations for the feedback platform."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class SlackIntegrationService:
    @staticmethod
    def is_enabled() -> bool:
        cfg = getattr(settings, "FEEDBACK_INTEGRATIONS", {}).get("slack", {})
        return bool(cfg.get("enabled") and (cfg.get("webhook_url") or cfg.get("bot_token")))

    @classmethod
    def notify(cls, text: str, *, event: str) -> bool:
        if not cls.is_enabled():
            logger.info("[Slack stub] %s: %s", event, text)
            return False

        cfg = settings.FEEDBACK_INTEGRATIONS["slack"]
        if event == "submit" and not cfg.get("notify_on_submit"):
            return False
        if event == "issue_created" and not cfg.get("notify_on_issue_created"):
            return False

        webhook = cfg.get("webhook_url")
        if not webhook:
            logger.info("[Slack stub] No webhook configured for %s", event)
            return False

        import requests

        payload: dict[str, Any] = {"text": text}
        channel = cfg.get("channel")
        if channel:
            payload["channel"] = channel

        response = requests.post(webhook, json=payload, timeout=15)
        response.raise_for_status()
        return True


class GitLabIntegrationService:
    @staticmethod
    def is_enabled() -> bool:
        cfg = getattr(settings, "FEEDBACK_INTEGRATIONS", {}).get("gitlab", {})
        return bool(cfg.get("enabled") and cfg.get("token") and cfg.get("project_id"))

    @classmethod
    def create_issue(cls, title: str, body: str, labels: list[str] | None = None) -> dict[str, Any] | None:
        if not cls.is_enabled():
            logger.info("[GitLab stub] Would create issue: %s", title)
            return None

        import requests

        cfg = settings.FEEDBACK_INTEGRATIONS["gitlab"]
        response = requests.post(
            f"{cfg['api_url']}/projects/{cfg['project_id']}/issues",
            headers={"PRIVATE-TOKEN": cfg["token"]},
            json={"title": title, "description": body, "labels": ",".join(labels or [])},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()


class JiraIntegrationService:
    @staticmethod
    def is_enabled() -> bool:
        cfg = getattr(settings, "FEEDBACK_INTEGRATIONS", {}).get("jira", {})
        return bool(
            cfg.get("enabled")
            and cfg.get("base_url")
            and cfg.get("email")
            and cfg.get("api_token")
            and cfg.get("project_key")
        )

    @classmethod
    def create_issue(cls, summary: str, description: str, issue_type: str = "Bug") -> dict[str, Any] | None:
        if not cls.is_enabled():
            logger.info("[Jira stub] Would create issue: %s", summary)
            return None

        import requests

        cfg = settings.FEEDBACK_INTEGRATIONS["jira"]
        response = requests.post(
            f"{cfg['base_url']}/rest/api/3/issue",
            auth=(cfg["email"], cfg["api_token"]),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={
                "fields": {
                    "project": {"key": cfg["project_key"]},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}],
                            }
                        ],
                    },
                    "issuetype": {"name": issue_type},
                }
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()


class AzureBoardsIntegrationService:
    @staticmethod
    def is_enabled() -> bool:
        cfg = getattr(settings, "FEEDBACK_INTEGRATIONS", {}).get("azure_boards", {})
        return bool(
            cfg.get("enabled")
            and cfg.get("organization")
            and cfg.get("project")
            and cfg.get("pat")
        )

    @classmethod
    def create_work_item(cls, title: str, description: str) -> dict[str, Any] | None:
        if not cls.is_enabled():
            logger.info("[Azure Boards stub] Would create work item: %s", title)
            return None

        import requests

        cfg = settings.FEEDBACK_INTEGRATIONS["azure_boards"]
        work_item_type = cfg.get("work_item_type", "Bug")
        org = cfg["organization"]
        project = cfg["project"]
        url = (
            f"{cfg['api_url']}/{org}/{project}/_apis/wit/workitems/$"
            f"{work_item_type}?api-version=7.1"
        )
        response = requests.post(
            url,
            auth=("", cfg["pat"]),
            headers={"Content-Type": "application/json-patch+json"},
            json=[
                {"op": "add", "path": "/fields/System.Title", "value": title},
                {"op": "add", "path": "/fields/System.Description", "value": description},
            ],
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
