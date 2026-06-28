from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.branches.models import Branch, BranchStatus
from apps.community.models import CommunityEvent, EventStatus, ForumCategory


class Command(BaseCommand):
    help = "Seed Epic 6 data: sample events and forum categories."

    @transaction.atomic
    def handle(self, *args, **options):
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

        now = timezone.now()
        events = [
            ("Guru Purnima Satsang", "Evening satsang and annadanam.", now + timedelta(days=14), now + timedelta(days=14, hours=3), 200),
            ("Vedic Chanting Workshop", "Open workshop on śikṣā and meter.", now + timedelta(days=30), now + timedelta(days=30, hours=2), 50),
        ]
        for title, desc, start, end, cap in events:
            CommunityEvent.objects.update_or_create(
                title=title,
                starts_at=start,
                defaults={
                    "description": desc,
                    "ends_at": end,
                    "capacity": cap,
                    "status": EventStatus.PUBLISHED,
                    "branch": branch,
                    "is_global": True,
                    "location": "HQ Campus",
                },
            )

        categories = [
            ("DHARMA", "Dharma Discussions", "Questions on śāstra, ethics, and daily practice."),
            ("ALUMNI", "Alumni Circle", "Reconnect, share experiences, and support current students."),
            ("STUDENT", "Student Lounge", "Peer support for coursework and hostel life."),
        ]
        for code, name, desc in categories:
            ForumCategory.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": desc, "branch": branch, "is_active": True},
            )

        self.stdout.write(self.style.SUCCESS("Epic 6 seed completed."))
