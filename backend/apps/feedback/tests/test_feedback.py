from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User, UserType
from apps.branches.models import Branch, UserBranchMembership
from apps.core.management.commands.seed_foundation import Command as SeedFoundation
from apps.feedback.models import Feedback, FeedbackAnalysis, FeedbackCategory, FeedbackModule, FeedbackStatus, GitHubIssueMapping
from apps.feedback.services import FeedbackAnalysisService, FeedbackWorkflowService, GitHubIntegrationService
from apps.rbac.models import Role, UserRoleAssignment


class FeedbackPlatformTests(TestCase):
    def setUp(self):
        SeedFoundation().handle()
        self.client = APIClient()
        self.branch = Branch.objects.first()
        self.student = User.objects.create_user(
            email="fbstudent@test.local",
            password="Student@FbTest12",
            user_type=UserType.STUDENT,
        )
        role = Role.objects.get(code="student")
        UserRoleAssignment.objects.create(user=self.student, role=role, branch=self.branch, is_active=True)
        UserBranchMembership.objects.create(user=self.student, branch=self.branch, is_active=True)
        self.client.force_authenticate(self.student)

    def test_ai_analysis_attendance_bug(self):
        fb = Feedback.objects.create(
            reporter=self.student,
            reporter_type="STUDENT",
            title="Attendance not saved",
            description="After marking attendance it shows success but disappears on refresh. Attendance module bug.",
            source_module=FeedbackModule.PLATFORM,
            category=FeedbackCategory.BUG,
        )
        analysis = FeedbackAnalysisService.analyze(fb)
        self.assertIn(analysis.ai_category, [FeedbackCategory.BUG, FeedbackCategory.PERFORMANCE])
        self.assertGreater(float(analysis.confidence), 0.6)
        self.assertTrue(analysis.ai_summary)

    def test_submit_api(self):
        admin = User.objects.get(email="admin@gurukulam.local")
        self.client.force_authenticate(admin)
        res = self.client.post(
            "/api/v1/feedback/submit/",
            {
                "title": "Slow lesson page",
                "description": "The lesson video is very slow to load in production.",
                "source_module": "LMS",
                "category": "PERFORMANCE",
                "environment": "PRODUCTION",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["success"])
        self.assertIn(res.data["data"]["status"], [
            FeedbackStatus.AI_ANALYZED,
            FeedbackStatus.PENDING_APPROVAL,
            FeedbackStatus.GITHUB_CREATED,
            FeedbackStatus.CLOSED,
        ])

    def test_appreciation_auto_closes(self):
        fb = Feedback.objects.create(
            reporter=self.student,
            reporter_type="STUDENT",
            title="Great platform",
            description="Thank you for the excellent curriculum and acharya support!",
            category=FeedbackCategory.APPRECIATION,
        )
        FeedbackWorkflowService.submit_and_process(fb, actor=self.student)
        fb.refresh_from_db()
        self.assertEqual(fb.status, FeedbackStatus.CLOSED)

    def test_anonymous_public_submit_rejected(self):
        self.client.force_authenticate(user=None)
        res = self.client.post(
            "/api/v1/feedback/submit/",
            {
                "title": "Website typo",
                "description": "Homepage has a spelling error",
            },
            format="json",
        )
        self.assertIn(res.status_code, (401, 403))

    def test_integrations_config_endpoint(self):
        admin = User.objects.get(email="admin@gurukulam.local")
        self.client.force_authenticate(admin)
        res = self.client.get("/api/v1/feedback/integrations/")
        self.assertEqual(res.status_code, 200)
        data = res.data["data"]
        self.assertEqual(data["issue_tracker"], "GITHUB")
        github = data["providers"]["github"]
        self.assertIn("github", data["providers"])
        self.assertIn("labels", github)
        self.assertIn("milestone", github)
        self.assertIn("project_configured", github)
        self.assertIn("auto_create_branch", github)
        self.assertIn("default_branch", github)
        self.assertIn("branch_prefix", github)
        self.assertIn("slack", data["providers"])
        self.assertNotIn("token", str(data).lower())

    @patch("apps.feedback.services.enrich_created_issue", return_value=({"branch_name": "", "milestone": "", "project_node_id": ""}, []))
    @patch("apps.feedback.services.GitHubIntegrationService.is_enabled", return_value=True)
    @patch("requests.post")
    def test_github_label_retry_on_422(self, mock_post, _enabled, _enrich):
        fb = Feedback.objects.create(
            reporter=self.student,
            reporter_type="STUDENT",
            title="Critical bug not saved",
            description="Attendance not saved after submission in production. Urgent bug.",
            source_module=FeedbackModule.ATTENDANCE,
            category=FeedbackCategory.BUG,
            severity="CRITICAL",
        )
        analysis = FeedbackAnalysisService.analyze(fb)
        fail = MagicMock(status_code=422, text='{"message":"Validation Failed"}')
        fail.json.return_value = {"message": "Validation Failed", "errors": [{"code": "invalid"}]}
        ok = MagicMock(status_code=201, text="{}")
        ok.json.return_value = {"number": 99, "html_url": "https://github.com/org/repo/issues/99", "labels": [], "node_id": "I_99"}
        mock_post.side_effect = [fail, ok]
        mapping, sync = GitHubIntegrationService.create_issue(fb, analysis)
        self.assertIsNotNone(mapping)
        self.assertTrue(sync.success)
        self.assertEqual(mapping.sync_mode, GitHubIssueMapping.SyncMode.REAL)
        self.assertEqual(mock_post.call_count, 2)
