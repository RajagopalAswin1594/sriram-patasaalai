from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.feedback.github_enrichment import (
    build_issue_branch_name,
    build_issue_create_payload,
    create_issue_branch,
    enrich_created_issue,
    resolve_milestone_number,
    slugify_branch,
)


class GitHubEnrichmentTests(TestCase):
    def test_slugify_branch(self):
        self.assertEqual(slugify_branch("Fix MFA Login Bug!"), "fix-mfa-login-bug")

    def test_build_issue_branch_name_custom_format(self):
        branch = build_issue_branch_name(
            issue_number=7,
            feedback_number="FB-2026-9DD2C9",
            gurukulam_id="HQ-01",
            title="The branch name should have the format of custom",
        )
        self.assertEqual(
            branch,
            "7-FB-2026-9DD2C9-HQ-01-the-branch-name-should-have-the-format-of-custom",
        )

    @patch("apps.feedback.github_enrichment.requests.get")
    def test_resolve_milestone_by_title(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"title": "Sprint 7", "number": 3}],
        )
        self.assertEqual(resolve_milestone_number("https://api.github.com", "org/repo", "token", "Sprint 7"), 3)

    @patch("apps.feedback.github_enrichment.requests.post")
    @patch("apps.feedback.github_enrichment.requests.get")
    def test_create_issue_branch(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"object": {"sha": "abc123"}},
        )
        mock_post.return_value = MagicMock(status_code=201, text="{}")
        branch, messages = create_issue_branch(
            "https://api.github.com",
            "org/repo",
            "token",
            42,
            "Fix login bug",
            feedback_number="FB-2026-000001",
            gurukulam_id="HQ-01",
            default_branch="main",
        )
        self.assertEqual(branch, "42-FB-2026-000001-HQ-01-fix-login-bug")
        self.assertTrue(any(m.code == "github_branch_created" for m in messages))
        mock_post.assert_called_once()
        self.assertIn("refs/heads/42-FB-2026-000001-HQ-01-fix-login-bug", mock_post.call_args.kwargs["json"]["ref"])

    @patch("apps.feedback.github_enrichment.create_issue_branch")
    @patch("apps.feedback.github_enrichment.add_issue_to_project_v2")
    def test_enrich_created_issue(self, mock_project, mock_branch):
        mock_project.return_value = []
        mock_branch.return_value = ("7-FB-2026-9DD2C9-HQ-01-slug", [])
        cfg = {"project_node_id": "PVT_1", "auto_create_branch": True, "milestone": "Sprint 7"}
        metadata, _ = enrich_created_issue(
            cfg,
            api_url="https://api.github.com",
            repo="org/repo",
            token="token",
            issue_data={"number": 7, "node_id": "I_1"},
            feedback_title="The branch name should have the format of custom",
            feedback_number="FB-2026-9DD2C9",
            gurukulam_id="HQ-01",
        )
        self.assertEqual(metadata["branch_name"], "7-FB-2026-9DD2C9-HQ-01-slug")
        mock_branch.assert_called_once()
        mock_project.assert_called_once_with("token", "PVT_1", "I_1")

    @patch("apps.feedback.github_enrichment.resolve_milestone_number", return_value=5)
    def test_build_issue_create_payload_includes_milestone(self, _milestone):
        payload = build_issue_create_payload(
            {"milestone": "Sprint 7"},
            api_url="https://api.github.com",
            repo="org/repo",
            token="token",
            title="Bug",
            body="Details",
            labels=["bug"],
        )
        self.assertEqual(payload["milestone"], 5)
        self.assertEqual(payload["labels"], ["bug"])
        self.assertNotIn("assignees", payload)
