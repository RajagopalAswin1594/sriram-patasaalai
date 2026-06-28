from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User, UserType
from apps.branches.models import Branch, UserBranchMembership
from apps.core.management.commands.seed_foundation import Command as SeedFoundation
from apps.gurukulam_feedback.models import GurukulamFeedbackStatus
from apps.rbac.models import Role, UserRoleAssignment


class GurukulamFeedbackTests(TestCase):
    def setUp(self):
        SeedFoundation().handle()
        self.client = APIClient()
        self.branch = Branch.objects.first()
        self.student = User.objects.create_user(
            email="gfstudent@test.local",
            password="Student@GfTest12",
            user_type=UserType.STUDENT,
        )
        role = Role.objects.get(code="student")
        UserRoleAssignment.objects.create(user=self.student, role=role, branch=self.branch, is_active=True)
        UserBranchMembership.objects.create(user=self.student, branch=self.branch, is_active=True)

    def test_student_can_submit_general_feedback(self):
        self.client.force_authenticate(self.student)
        res = self.client.post(
            "/api/v1/gurukulam-feedback/submit/",
            {
                "title": "Mess food quality",
                "description": "Would appreciate more variety in the weekly mess menu.",
                "category": "HOSTEL",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["data"]["status"], GurukulamFeedbackStatus.SUBMITTED)

    def test_anonymous_can_submit(self):
        res = self.client.post(
            "/api/v1/gurukulam-feedback/submit/",
            {
                "title": "Visitor suggestion",
                "description": "The campus tour was wonderful.",
                "category": "APPRECIATION",
                "is_anonymous": True,
                "reporter_email": "visitor@example.com",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)

    def test_student_cannot_submit_dev_feedback(self):
        self.client.force_authenticate(self.student)
        res = self.client.post(
            "/api/v1/feedback/submit/",
            {"title": "Bug", "description": "App crash"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_super_admin_can_submit_dev_feedback(self):
        admin = User.objects.get(email="admin@gurukulam.local")
        self.client.force_authenticate(admin)
        res = self.client.post(
            "/api/v1/feedback/submit/",
            {
                "title": "Slow API",
                "description": "Admissions list endpoint is slow in production.",
                "source_module": "ADMISSIONS",
                "category": "PERFORMANCE",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
