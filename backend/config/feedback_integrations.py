"""Feedback platform integration settings (issue trackers + Slack)."""

from __future__ import annotations

from typing import Any


def load_feedback_integration_settings(env) -> dict[str, Any]:
    issue_tracker = env("FEEDBACK_ISSUE_TRACKER", default="GITHUB").upper()
    auto_create = env.bool("FEEDBACK_AUTO_CREATE_ISSUE", default=env.bool("FEEDBACK_AUTO_GITHUB", default=False))

    github = {
        "enabled": env.bool("GITHUB_ENABLED", default=False),
        "token": env("GITHUB_TOKEN", default="").strip(),
        "repo": env("GITHUB_REPO", default="").strip(),
        "api_url": env("GITHUB_API_URL", default="https://api.github.com").rstrip("/"),
        "labels": env("GITHUB_LABELS", default=""),
        "milestone": env("GITHUB_MILESTONE", default="").strip(),
        "project_node_id": env("GITHUB_PROJECT_NODE_ID", default="").strip(),
        "default_branch": env("GITHUB_DEFAULT_BRANCH", default="").strip(),
        "branch_prefix": env("GITHUB_BRANCH_PREFIX", default="").strip(),
        "auto_create_branch": env.bool("GITHUB_AUTO_CREATE_BRANCH", default=True),
    }
    gitlab = {
        "enabled": env.bool("GITLAB_ENABLED", default=False),
        "token": env("GITLAB_TOKEN", default=""),
        "project_id": env("GITLAB_PROJECT_ID", default=""),
        "api_url": env("GITLAB_API_URL", default="https://gitlab.com/api/v4").rstrip("/"),
    }
    jira = {
        "enabled": env.bool("JIRA_ENABLED", default=False),
        "base_url": env("JIRA_BASE_URL", default="").rstrip("/"),
        "email": env("JIRA_EMAIL", default=""),
        "api_token": env("JIRA_API_TOKEN", default=""),
        "project_key": env("JIRA_PROJECT_KEY", default=""),
    }
    azure_boards = {
        "enabled": env.bool("AZURE_BOARDS_ENABLED", default=False),
        "organization": env("AZURE_DEVOPS_ORG", default=""),
        "project": env("AZURE_DEVOPS_PROJECT", default=""),
        "pat": env("AZURE_DEVOPS_PAT", default=""),
        "work_item_type": env("AZURE_BOARDS_WORK_ITEM_TYPE", default="Bug"),
        "api_url": env(
            "AZURE_DEVOPS_API_URL",
            default="https://dev.azure.com",
        ).rstrip("/"),
    }
    slack = {
        "enabled": env.bool("SLACK_ENABLED", default=False),
        "bot_token": env("SLACK_BOT_TOKEN", default=""),
        "webhook_url": env("SLACK_WEBHOOK_URL", default=""),
        "channel": env("SLACK_CHANNEL", default="#feedback-ops"),
        "notify_on_submit": env.bool("SLACK_NOTIFY_ON_SUBMIT", default=False),
        "notify_on_issue_created": env.bool("SLACK_NOTIFY_ON_ISSUE_CREATED", default=True),
    }

    # Auto-enable GitHub when legacy token/repo are set without an explicit flag.
    if not github["enabled"] and github["token"] and github["repo"]:
        github["enabled"] = True

    trackers = {
        "GITHUB": github,
        "GITLAB": gitlab,
        "JIRA": jira,
        "AZURE_BOARDS": azure_boards,
    }

    return {
        "general": {
            "default_env": env("FEEDBACK_DEFAULT_ENV", default="PRODUCTION"),
            "issue_tracker": issue_tracker,
            "auto_create_issue": auto_create,
        },
        "github": github,
        "gitlab": gitlab,
        "jira": jira,
        "azure_boards": azure_boards,
        "slack": slack,
        "active_tracker": trackers.get(issue_tracker, github),
    }


def integration_status(settings) -> dict[str, bool]:
    """Summarize which integrations are configured (for ops / health checks)."""
    integrations = getattr(settings, "FEEDBACK_INTEGRATIONS", {})
    github = integrations.get("github", {})
    gitlab = integrations.get("gitlab", {})
    jira = integrations.get("jira", {})
    azure = integrations.get("azure_boards", {})
    slack = integrations.get("slack", {})
    return {
        "github": bool(github.get("enabled") and github.get("token") and github.get("repo")),
        "gitlab": bool(gitlab.get("enabled") and gitlab.get("token") and gitlab.get("project_id")),
        "jira": bool(
            jira.get("enabled")
            and jira.get("base_url")
            and jira.get("email")
            and jira.get("api_token")
            and jira.get("project_key")
        ),
        "azure_boards": bool(
            azure.get("enabled")
            and azure.get("organization")
            and azure.get("project")
            and azure.get("pat")
        ),
        "slack": bool(slack.get("enabled") and (slack.get("webhook_url") or slack.get("bot_token"))),
    }
