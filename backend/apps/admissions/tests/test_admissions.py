from django.test import TestCase
from rest_framework.test import APIClient

from apps.branches.models import Branch
from apps.core.management.commands.seed_foundation import Command as SeedCommand


class AdmissionsAPITestCase(TestCase):
    def setUp(self):
        SeedCommand().handle()
        self.client = APIClient()
        self.branch = Branch.objects.get(code="HQ-01")

    def test_public_branch_list(self):
        response = self.client.get("/api/v1/admissions/branches/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()["data"]), 1)

    def test_create_and_submit_application_flow(self):
        create = self.client.post(
            "/api/v1/admissions/applications/",
            {
                "branch_id": str(self.branch.id),
                "student_first_name": "Arjun",
                "date_of_birth": "2012-03-10",
                "grade_applying": "Prathama",
                "parent_name": "Ravi Kumar",
                "parent_phone": "9876543210",
                "address_line_1": "12 Temple Street",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "postal_code": "600001",
                "data_consent": True,
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        app = create.json()["data"]
        token = app["access_token"]
        app_id = app["id"]

        presign = self.client.post(
            f"/api/v1/admissions/applications/{app_id}/documents/presign/",
            {
                "access_token": token,
                "document_type": "STUDENT_PHOTO",
                "file_name": "photo.jpg",
                "content_type": "image/jpeg",
                "file_size": 1024,
            },
            format="json",
        )
        self.assertEqual(presign.status_code, 200)
        document_id = presign.json()["data"]["document_id"]
        upload = presign.json()["data"]["upload"]

        upload_response = self.client.post(
            "/api/v1/admissions/uploads/local/",
            {"key": upload["fields"]["key"]},
            format="multipart",
        )
        # Without file in test multipart is incomplete; confirm upload directly for local dev path
        confirm = self.client.post(
            f"/api/v1/admissions/applications/{app_id}/documents/confirm/",
            {"access_token": token, "document_id": document_id},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200)

        self.client.post(
            f"/api/v1/admissions/applications/{app_id}/documents/presign/",
            {
                "access_token": token,
                "document_type": "BIRTH_CERTIFICATE",
                "file_name": "birth.pdf",
                "content_type": "application/pdf",
                "file_size": 2048,
            },
            format="json",
        )
        birth_presign = self.client.post(
            f"/api/v1/admissions/applications/{app_id}/documents/presign/",
            {
                "access_token": token,
                "document_type": "BIRTH_CERTIFICATE",
                "file_name": "birth.pdf",
                "content_type": "application/pdf",
                "file_size": 2048,
            },
            format="json",
        )
        birth_id = birth_presign.json()["data"]["document_id"]
        self.client.post(
            f"/api/v1/admissions/applications/{app_id}/documents/confirm/",
            {"access_token": token, "document_id": birth_id},
            format="json",
        )

        submit = self.client.post(
            f"/api/v1/admissions/applications/{app_id}/submit/",
            {"access_token": token},
            format="json",
        )
        self.assertEqual(submit.status_code, 200)

        pay_init = self.client.post(
            f"/api/v1/admissions/applications/{app_id}/payment/initiate/",
            {"access_token": token},
            format="json",
        )
        self.assertEqual(pay_init.status_code, 200)
        self.assertTrue(pay_init.json()["data"].get("demo_mode"))

        pay_confirm = self.client.post(
            f"/api/v1/admissions/applications/{app_id}/payment/confirm/",
            {"access_token": token},
            format="json",
        )
        self.assertEqual(pay_confirm.status_code, 200)
        self.assertEqual(pay_confirm.json()["data"]["status"], "PENDING")
