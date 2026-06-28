from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import AccountStatus, User, UserType
from apps.branches.models import Branch, BranchStatus, UserBranchMembership
from apps.core.management.commands.seed_foundation import Command as SeedCommand
from apps.rbac.models import Role, UserRoleAssignment


class AuthAPITestCase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.client = APIClient()
        self.admin = User.objects.get(email="admin@gurukulam.local")
        self.branch = Branch.objects.get(code="HQ-01")

    def test_health_check(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_login_success(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "Admin@Gurukulam1"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("access", data["tokens"])
        self.assertEqual(data["user"]["email"], "admin@gurukulam.local")

    def test_login_invalid_credentials(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_me_requires_auth(self):
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_permissions(self):
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "Admin@Gurukulam1"},
            format="json",
        )
        token = login.json()["data"]["tokens"]["access"]
        response = self.client.get(
            "/api/v1/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()["data"]
        self.assertTrue(body["is_super_admin"])
        self.assertIn("*", body["permissions"])


class RBACAPITestCase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.client = APIClient()
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "Admin@Gurukulam1"},
            format="json",
        )
        self.token = login.json()["data"]["tokens"]["access"]
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_list_permissions(self):
        response = self.client.get("/api/v1/permissions/", **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 10)

    def test_list_roles(self):
        response = self.client.get("/api/v1/roles/", **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 7)


class UserBranchAPITestCase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.client = APIClient()
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "Admin@Gurukulam1"},
            format="json",
        )
        self.token = login.json()["data"]["tokens"]["access"]
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        self.branch = Branch.objects.get(code="HQ-01")

    def test_create_user(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "email": "student1@gurukulam.local",
                "password": "Student@Pass123",
                "user_type": UserType.STUDENT,
                "profile": {"first_name": "Rama", "last_name": "Shishya"},
                "type_profile": {"date_of_birth": "2010-05-15"},
            },
            format="json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 201)
        user_id = response.json()["data"]["id"]

        membership = self.client.post(
            "/api/v1/branch-memberships/",
            {"user_id": user_id, "branch_id": str(self.branch.id), "is_primary": True},
            format="json",
            **self.auth,
        )
        self.assertEqual(membership.status_code, 201)

        student_role = Role.objects.get(code="student")
        assignment = self.client.post(
            "/api/v1/role-assignments/",
            {
                "user_id": user_id,
                "role_id": str(student_role.id),
                "branch_id": str(self.branch.id),
            },
            format="json",
            **self.auth,
        )
        self.assertEqual(assignment.status_code, 201)

    def test_list_branches(self):
        response = self.client.get("/api/v1/branches/", **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 1)
