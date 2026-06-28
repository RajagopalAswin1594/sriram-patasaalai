from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.admissions.models import ApplicationNotification, ApplicationStatus, ApplicationStatusHistory
from apps.branches.models import Branch
from apps.core.management.commands.seed_foundation import Command as SeedCommand


class ReviewWorkflowTestCase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.client = APIClient()
        self.branch = Branch.objects.get(code="HQ-01")
        self.admin = User.objects.get(email="admin@gurukulam.local")
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "admin@gurukulam.local", "password": "Admin@Gurukulam1"},
            format="json",
        )
        self.token = login.json()["data"]["tokens"]["access"]
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

        create = self.client.post(
            "/api/v1/admissions/applications/",
            {
                "branch_id": str(self.branch.id),
                "student_first_name": "Kavya",
                "date_of_birth": "2011-08-20",
                "grade_applying": "Prathama",
                "parent_name": "Lakshmi",
                "parent_phone": "9123456780",
                "parent_email": "parent@example.com",
                "address_line_1": "1 Temple Road",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "postal_code": "600001",
                "data_consent": True,
            },
            format="json",
        )
        self.app = create.json()["data"]
        self._complete_application()

    def _complete_application(self):
        app_id = self.app["id"]
        token = self.app["access_token"]
        for doc_type, fname, ctype in [
            ("STUDENT_PHOTO", "p.jpg", "image/jpeg"),
            ("BIRTH_CERTIFICATE", "b.pdf", "application/pdf"),
        ]:
            presign = self.client.post(
                f"/api/v1/admissions/applications/{app_id}/documents/presign/",
                {
                    "access_token": token,
                    "document_type": doc_type,
                    "file_name": fname,
                    "content_type": ctype,
                    "file_size": 1024,
                },
                format="json",
            )
            doc_id = presign.json()["data"]["document_id"]
            self.client.post(
                f"/api/v1/admissions/applications/{app_id}/documents/confirm/",
                {"access_token": token, "document_id": doc_id},
                format="json",
            )
        self.client.post(f"/api/v1/admissions/applications/{app_id}/submit/", {"access_token": token}, format="json")
        self.client.post(f"/api/v1/admissions/applications/{app_id}/payment/initiate/", {"access_token": token}, format="json")
        self.client.post(f"/api/v1/admissions/applications/{app_id}/payment/confirm/", {"access_token": token}, format="json")

    def test_payment_moves_to_pending_with_history(self):
        self.assertEqual(self.app["id"], self.app["id"])
        detail = self.client.get(f"/api/v1/admissions/admin/applications/{self.app['id']}/", **self.auth)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["status"], ApplicationStatus.PENDING)
        self.assertGreaterEqual(ApplicationStatusHistory.objects.filter(application_id=self.app["id"]).count(), 1)

    def test_approve_triggers_notification_audit(self):
        review = self.client.post(
            f"/api/v1/admissions/admin/applications/{self.app['id']}/review/",
            {"status": "APPROVED", "review_notes": "Excellent candidate"},
            format="json",
            **self.auth,
        )
        self.assertEqual(review.status_code, 200)
        self.assertEqual(review.json()["data"]["status"], ApplicationStatus.APPROVED)
        self.assertTrue(
            ApplicationNotification.objects.filter(
                application_id=self.app["id"],
                event_type="APPLICATION_APPROVED",
            ).exists()
        )

    def test_admin_stats(self):
        response = self.client.get("/api/v1/admissions/admin/stats/", **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["data"]["pending"], 1)

    def test_admin_document_view_inline(self):
        from pathlib import Path

        from django.conf import settings

        from apps.admissions.models import ApplicationDocument

        app_id = self.app["id"]
        document = ApplicationDocument.objects.filter(application_id=app_id, document_type="STUDENT_PHOTO").first()
        self.assertIsNotNone(document)
        target = Path(settings.MEDIA_ROOT) / document.s3_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fake-image-bytes")

        response = self.client.get(
            f"/api/v1/admissions/admin/applications/{app_id}/documents/{document.id}/view/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"fake-image-bytes")

    def test_admin_document_review_approve(self):
        from pathlib import Path

        from django.conf import settings

        from apps.admissions.models import (
            ApplicationDocument,
            ApplicationDocumentReviewLog,
            ApplicationNotification,
            DocumentUploadStatus,
        )

        app_id = self.app["id"]
        document = ApplicationDocument.objects.filter(application_id=app_id, document_type="STUDENT_PHOTO").first()
        target = Path(settings.MEDIA_ROOT) / document.s3_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fake-image-bytes")

        response = self.client.post(
            f"/api/v1/admissions/admin/applications/{app_id}/documents/{document.id}/review/",
            {"action": "APPROVE", "notify_channels": ["EMAIL", "WHATSAPP"]},
            format="json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.upload_status, DocumentUploadStatus.VERIFIED)
        self.assertTrue(ApplicationDocumentReviewLog.objects.filter(document=document, action="APPROVE").exists())
        self.assertTrue(
            ApplicationNotification.objects.filter(
                application_id=app_id,
                event_type="DOCUMENT_VERIFIED",
            ).exists()
        )

    def test_admin_document_review_resubmit_requires_reason(self):
        from apps.admissions.models import ApplicationDocument

        app_id = self.app["id"]
        document = ApplicationDocument.objects.filter(application_id=app_id, document_type="BIRTH_CERTIFICATE").first()
        response = self.client.post(
            f"/api/v1/admissions/admin/applications/{app_id}/documents/{document.id}/review/",
            {"action": "REQUEST_RESUBMIT", "notify_channels": ["SMS"]},
            format="json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 400)

    def test_reject_requires_reason_optional(self):
        app2 = self.client.post(
            "/api/v1/admissions/applications/",
            {
                "branch_id": str(self.branch.id),
                "student_first_name": "RejectMe",
                "date_of_birth": "2011-01-01",
                "grade_applying": "Prathama",
                "parent_name": "Parent",
                "parent_phone": "9000000001",
                "address_line_1": "Addr",
                "city": "Chennai",
                "state": "TN",
                "postal_code": "600001",
                "data_consent": True,
            },
            format="json",
        ).json()["data"]
        self.app = app2
        self._complete_application()
        response = self.client.post(
            f"/api/v1/admissions/admin/applications/{app2['id']}/review/",
            {"status": "REJECTED", "rejection_reason": "Incomplete documentation"},
            format="json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], ApplicationStatus.REJECTED)
