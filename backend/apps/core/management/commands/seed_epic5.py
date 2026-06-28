from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.branches.models import Branch, BranchStatus
from apps.donations.models import DonationCategory
from apps.hostel.models import Hostel, HostelRoom
from apps.notifications.models import NotificationChannel, NotificationTemplate


class Command(BaseCommand):
    help = "Seed Epic 5 data: donation categories, notification templates, sample hostel."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = [
            ("ANNADANAM_MEALS", "Annadanam (Meals)", "Sponsor daily meals for students.", Decimal("500")),
            ("GENERAL", "General Donation", "General fund for Gurukulam operations.", Decimal("100")),
            ("STUDENT_SPONSORSHIP", "Student Sponsorship", "Sponsor a student's education and boarding.", Decimal("5000")),
            ("ACHARYA_SPONSORSHIP", "Acharya Sponsorship", "Support an acharya's teaching and research.", Decimal("10000")),
        ]
        for code, name, desc, min_amt in categories:
            DonationCategory.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": desc, "min_amount": min_amt, "is_active": True},
            )

        templates = [
            (
                "DONATION_RECEIPT",
                "Donation Tax Receipt",
                NotificationChannel.EMAIL,
                "Donation Receipt – {{ receipt_number }}",
                "Dear {{ donor_name }},\n\nThank you for your donation of ₹{{ amount }} towards {{ category }}.\n"
                "Receipt: {{ receipt_number }}\n\nThis receipt is valid under Section 80G.\n\n– Gurukulam",
            ),
            (
                "HOSTEL_LEAVE_ALERT",
                "Hostel Leave Alert",
                NotificationChannel.SMS,
                "",
                "Student {{ student_name }} is now {{ leave_status }} in {{ hostel_name }}.",
            ),
            (
                "HOSTEL_LEAVE_ALERT",
                "Hostel Leave Alert (WhatsApp)",
                NotificationChannel.WHATSAPP,
                "",
                "Student {{ student_name }} is now {{ leave_status }} in {{ hostel_name }}.",
            ),
        ]
        for code, name, channel, subject, body in templates:
            NotificationTemplate.objects.update_or_create(
                code=code,
                channel=channel,
                defaults={
                    "name": name,
                    "subject_template": subject,
                    "body_template": body,
                    "is_active": True,
                },
            )

        branch = Branch.objects.filter(is_headquarters=True).first() or Branch.objects.first()
        if not branch:
            branch = Branch.objects.create(
                code="HQ-01",
                name="Headquarters",
                slug="headquarters",
                status=BranchStatus.ACTIVE,
                city="Chennai",
                state="Tamil Nadu",
                country="IN",
                is_headquarters=True,
            )
        if branch:
            hostel, _ = Hostel.objects.update_or_create(
                branch=branch,
                code="HQ-HOSTEL-1",
                defaults={
                    "name": "HQ Boys Hostel",
                    "address": "Campus Block A",
                    "capacity": 40,
                },
            )
            for num, floor in [("101", "1"), ("102", "1"), ("201", "2")]:
                HostelRoom.objects.update_or_create(
                    hostel=hostel,
                    room_number=num,
                    defaults={"floor": floor, "capacity": 2},
                )

        self.stdout.write(self.style.SUCCESS("Epic 5 seed completed."))
