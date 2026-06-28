from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.academics.models import AcademicYear, Batch, BatchCourse, Shakha, VedicCourse
from apps.branches.models import Branch


class Command(BaseCommand):
    help = "Seed Epic 2 academics data: shakhas, courses, academic year, sample batch."

    @transaction.atomic
    def handle(self, *args, **options):
        branch = Branch.objects.filter(code="HQ-01", is_deleted=False).first()
        if not branch:
            self.stderr.write("Run seed_foundation first.")
            return

        shakhas = {}
        for code, name in [
            ("YAJUR", "Yajur Veda"),
            ("RIG", "Rig Veda"),
            ("SAMA", "Sama Veda"),
            ("ATHARVA", "Atharva Veda"),
        ]:
            shakha, _ = Shakha.objects.get_or_create(code=code, defaults={"name": name})
            shakhas[code] = shakha

        year, _ = AcademicYear.objects.get_or_create(
            name="2025-2026",
            defaults={
                "starts_on": date(2025, 6, 1),
                "ends_on": date(2026, 5, 31),
                "is_current": True,
            },
        )

        courses = {}
        for code, name, shakha_code, grade in [
            ("YAJ-PRA-1", "Yajur Prathama", "YAJUR", "Prathama"),
            ("RIG-PRA-1", "Rig Prathama", "RIG", "Prathama"),
        ]:
            course, _ = VedicCourse.objects.get_or_create(
                code=code,
                shakha=shakhas[shakha_code],
                defaults={"name": name, "grade_level": grade},
            )
            courses[code] = course

        batch, _ = Batch.objects.get_or_create(
            branch=branch,
            academic_year=year,
            code="YAJ-PRA-A",
            defaults={"name": "Yajur Prathama – Morning A", "capacity": 25, "is_active": True},
        )
        BatchCourse.objects.get_or_create(batch=batch, course=courses["YAJ-PRA-1"])

        self.stdout.write(self.style.SUCCESS("Epic 2 seed completed."))
        self.stdout.write(f"Shakhas: {len(shakhas)}, Batch: {batch.code}")
