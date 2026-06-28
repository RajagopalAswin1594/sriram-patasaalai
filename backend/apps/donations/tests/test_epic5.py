from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User, UserType
from apps.branches.models import Branch, UserBranchMembership
from apps.core.management.commands.seed_epic5 import Command as SeedEpic5
from apps.donations.models import Donation, DonationStatus
from apps.donations.payment import DonationPaymentService
from apps.hostel.models import Hostel, HostelRoom
from apps.hostel.services import HostelService
from apps.notifications.models import NotificationLog
from apps.notifications.services import NotificationDispatcher


class Epic5Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        SeedEpic5().handle()
        self.branch = Branch.objects.first()
        self.admin = User.objects.create_superuser(email="epic5admin@test.local", password="Admin@Epic5Test")
        if self.branch:
            UserBranchMembership.objects.get_or_create(
                user=self.admin,
                branch=self.branch,
                defaults={"is_primary": True, "is_active": True},
            )
        self.student = User.objects.create_user(
            email="epic5student@test.local",
            password="Student@Epic5Test",
            user_type=UserType.STUDENT,
        )
        self.client.force_authenticate(self.admin)

    def test_public_donation_demo_flow(self):
        res = self.client.post(
            "/api/v1/donations/initiate/",
            {
                "category_code": "GENERAL",
                "amount": "250.00",
                "donor_name": "Test Donor",
                "donor_email": "donor@test.local",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        donation_id = res.data["data"]["donation"]["id"]
        confirm = self.client.post("/api/v1/donations/confirm/", {"donation_id": donation_id}, format="json")
        self.assertEqual(confirm.status_code, 200)
        self.assertEqual(confirm.data["data"]["status"], DonationStatus.COMPLETED)
        self.assertTrue(Donation.objects.get(id=donation_id).receipt)

    def test_webhook_idempotency(self):
        donation, _ = DonationPaymentService.initiate(
            {
                "category_code": "GENERAL",
                "amount": Decimal("100"),
                "donor_name": "Webhook Donor",
            }
        )
        donation.gateway_order_id = "order_test123"
        donation.save()
        event = {
            "id": "evt_unique_1",
            "payload": {"payment": {"entity": {"order_id": "order_test123", "id": "pay_test123"}}},
        }
        r1 = DonationPaymentService.handle_webhook(event)
        r2 = DonationPaymentService.handle_webhook(event)
        self.assertEqual(r1["status"], "completed")
        self.assertEqual(r2["status"], "already_processed")

    def test_hostel_assignment_and_leave(self):
        hostel = Hostel.objects.first()
        room = HostelRoom.objects.filter(hostel=hostel).first()
        assignment = HostelService.assign_student(room, self.student, check_in=date(2026, 1, 1))
        self.assertTrue(assignment.mess_eligible)
        updated = HostelService.update_leave_status(assignment, "ON_LEAVE")
        self.assertFalse(updated.mess_eligible)
        map_data = HostelService.occupancy_map(self.admin)
        self.assertTrue(len(map_data) >= 1)

    def test_notification_idempotency(self):
        NotificationDispatcher.send(
            template_code="DONATION_RECEIPT",
            recipient_email="test@example.com",
            context={"donor_name": "A", "amount": "100", "receipt_number": "R1", "category": "General"},
            idempotency_key="test-key-1",
            channels=["EMAIL"],
        )
        NotificationDispatcher.send(
            template_code="DONATION_RECEIPT",
            recipient_email="test@example.com",
            context={"donor_name": "A", "amount": "100", "receipt_number": "R1", "category": "General"},
            idempotency_key="test-key-1",
            channels=["EMAIL"],
        )
        self.assertEqual(NotificationLog.objects.filter(idempotency_key="test-key-1").count(), 1)
