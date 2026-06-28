from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import VedicCourse
from apps.core.management.commands.seed_epic2 import Command as SeedEpic2Command
from apps.core.management.commands.seed_foundation import Command as SeedCommand
from apps.curriculum.models import SyllabusStatus
from apps.curriculum.services import SyllabusService
from apps.learning.services import ExamScoreService


class Epic34TestCase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        SeedEpic2Command().handle()
        self.client = APIClient()
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "Admin@Gurukulam1"},
            format="json",
        )
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {login.json()['data']['tokens']['access']}"}
        self.course = VedicCourse.objects.first()

    def test_syllabus_version_and_publish(self):
        create = self.client.post(
            "/api/v1/curriculum/syllabi/",
            {"course_id": str(self.course.id), "version_label": "v1.0"},
            format="json",
            **self.auth,
        )
        self.assertEqual(create.status_code, 201)
        syllabus_id = create.json()["data"]["id"]
        module = self.client.post(
            "/api/v1/curriculum/modules/",
            {"syllabus": syllabus_id, "title": "Prathama – Pada 1", "title_sa": "प्रथमा", "sort_order": 1},
            format="json",
            **self.auth,
        )
        self.assertEqual(module.status_code, 201)
        publish = self.client.post(f"/api/v1/curriculum/syllabi/{syllabus_id}/publish/", **self.auth)
        self.assertEqual(publish.status_code, 200)
        self.assertEqual(publish.json()["data"]["status"], SyllabusStatus.PUBLISHED)

    def test_exam_score_revision_log(self):
        from apps.academics.models import Batch
        from apps.accounts.models import User, UserType
        from apps.learning.models import Exam, ExamScoreRevision

        from apps.accounts.models import User

        batch = Batch.objects.first()
        admin = User.objects.get(email="admin@gurukulam.local")
        student = User.objects.create_user(
            email="exam.student@test.local",
            password="Student@123456",
            user_type=UserType.STUDENT,
        )
        exam = Exam.objects.create(
            batch=batch,
            course=self.course,
            title="Oral Pariksha",
            scheduled_at=timezone.now(),
            acharya=admin,
        )
        ExamScoreService.upsert_score(exam, student, 80, oral_grade="Kizham")
        ExamScoreService.upsert_score(exam, student, 90, oral_grade="Madhyamam", entered_by=None, reason="Re-evaluation")
        self.assertEqual(ExamScoreRevision.objects.count(), 1)

    def test_certificate_verify_public(self):
        from apps.accounts.models import User, UserType
        from apps.academics.models import Batch
        from apps.certifications.services import CertificateService

        student = User.objects.create_user(
            email="cert.student@test.local",
            password="Student@123456",
            user_type=UserType.STUDENT,
        )
        batch = Batch.objects.first()
        cert = CertificateService.issue(student, self.course, batch, None, batch.branch.name)
        verify = self.client.get(f"/api/v1/certifications/verify/{cert.verification_code}/")
        self.assertEqual(verify.status_code, 200)
        self.assertEqual(verify.json()["data"]["certificate_number"], cert.certificate_number)
