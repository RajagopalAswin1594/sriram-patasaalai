from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import Batch, Shakha
from apps.accounts.models import User, UserType
from apps.branches.models import Branch
from apps.core.management.commands.seed_epic2 import Command as SeedEpic2Command
from apps.core.management.commands.seed_foundation import Command as SeedCommand
from apps.scheduling.models import TeachingSession
from apps.students.models import BatchEnrollment, ParentChildLink, StudentBranchEnrollment
from apps.students.services import StudentEnrollmentService


class Epic2TestCase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        SeedEpic2Command().handle()
        self.client = APIClient()
        self.branch = Branch.objects.get(code="HQ-01")
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "Admin@Gurukulam1"},
            format="json",
        )
        self.token = login.json()["data"]["tokens"]["access"]
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        self.batch = Batch.objects.get(code="YAJ-PRA-A")

    def test_create_student_and_bulk_assign(self):
        create = self.client.post(
            "/api/v1/students/create/",
            {
                "email": "arjun.student@gurukulam.local",
                "password": "Student@123",
                "branch_id": str(self.branch.id),
                "batch_id": str(self.batch.id),
                "profile": {"first_name": "Arjun", "last_name": "Kumar"},
                "type_profile": {"admission_number": "STU-001", "date_of_birth": "2012-03-10"},
            },
            format="json",
            **self.auth,
        )
        self.assertEqual(create.status_code, 201)
        student_id = create.json()["data"]["user"]["id"]
        self.assertTrue(StudentBranchEnrollment.objects.filter(student_id=student_id).exists())
        self.assertTrue(BatchEnrollment.objects.filter(student_enrollment__student_id=student_id).exists())

    def test_parent_child_link_scoping(self):
        user, _enrollment = StudentEnrollmentService.create_active_student(
            {
                "email": "kavya.student@gurukulam.local",
                "password": "Student@123",
                "branch_id": self.branch.id,
                "profile": {"first_name": "Kavya"},
                "type_profile": {"admission_number": "STU-002"},
            },
            actor=None,
        )
        student_user = user

        parent_resp = self.client.post(
            "/api/v1/users/",
            {
                "email": "parent@gurukulam.local",
                "password": "Parent@123456",
                "user_type": "PARENT",
                "profile": {"first_name": "Lakshmi"},
                "type_profile": {"relationship_type": "MOTHER"},
            },
            format="json",
            **self.auth,
        )
        parent_id = parent_resp.json()["data"]["id"]
        link = self.client.post(
            "/api/v1/students/parent-links/",
            {
                "parent_id": parent_id,
                "student_id": str(student_user.id),
                "relationship_type": "MOTHER",
            },
            format="json",
            **self.auth,
        )
        self.assertEqual(link.status_code, 201)
        self.assertTrue(ParentChildLink.objects.filter(parent_id=parent_id, student=student_user).exists())

    def test_batch_transfer_preserves_history(self):
        user, _enrollment = StudentEnrollmentService.create_active_student(
            {
                "email": "transfer.student@gurukulam.local",
                "password": "Student@123",
                "branch_id": self.branch.id,
                "batch_id": self.batch.id,
                "profile": {"first_name": "Transfer"},
                "type_profile": {"admission_number": "STU-003"},
            },
            actor=None,
        )
        year = self.batch.academic_year
        shakha = Shakha.objects.first()
        from apps.academics.models import VedicCourse

        course, _ = VedicCourse.objects.get_or_create(
            code="RIG-PRA-2",
            shakha=shakha,
            defaults={"name": "Rig Prathama B", "grade_level": "Prathama"},
        )
        new_batch = Batch.objects.create(
            branch=self.branch,
            academic_year=year,
            code="RIG-PRA-B",
            name="Rig Prathama – Morning B",
        )
        from apps.academics.models import BatchCourse

        BatchCourse.objects.create(batch=new_batch, course=course)

        StudentEnrollmentService.transfer_batch(
            user.id,
            self.batch.id,
            new_batch.id,
            reason="Mid-year shakha change",
        )
        branch_enrollment = StudentBranchEnrollment.objects.get(student=user, branch=self.branch)
        self.assertEqual(BatchEnrollment.objects.filter(student_enrollment=branch_enrollment).count(), 2)

    def test_acharya_registration_and_conflict(self):
        shakha = Shakha.objects.first()
        register = self.client.post(
            "/api/v1/scheduling/acharyas/register/",
            {
                "email": "acharya@gurukulam.local",
                "password": "Acharya@123",
                "branch_ids": [str(self.branch.id)],
                "shakha_ids": [str(shakha.id)],
                "profile": {"first_name": "Venkatesh"},
                "type_profile": {"employee_code": "ACH-01", "specialization": "Yajur Veda"},
            },
            format="json",
            **self.auth,
        )
        self.assertEqual(register.status_code, 201)
        acharya_id = register.json()["data"]["id"]
        starts = timezone.now() + timedelta(days=1)
        ends = starts + timedelta(hours=1)
        payload = {
            "acharya_id": acharya_id,
            "batch_id": str(self.batch.id),
            "branch_id": str(self.branch.id),
            "title": "Prathama – Pada 1",
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "timezone": "Asia/Kolkata",
        }
        first = self.client.post("/api/v1/scheduling/sessions/", payload, format="json", **self.auth)
        self.assertEqual(first.status_code, 201)
        conflict = self.client.post("/api/v1/scheduling/sessions/", payload, format="json", **self.auth)
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(TeachingSession.objects.filter(acharya_id=acharya_id).count(), 1)
