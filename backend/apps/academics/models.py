from django.db import models

from apps.core.models import AuditableModel


class Shakha(AuditableModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AcademicYear(AuditableModel):
    name = models.CharField(max_length=30)
    starts_on = models.DateField()
    ends_on = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_on"]

    def __str__(self):
        return self.name


class VedicCourse(AuditableModel):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    shakha = models.ForeignKey(Shakha, on_delete=models.PROTECT, related_name="courses")
    grade_level = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["grade_level", "name"]
        constraints = [
            models.UniqueConstraint(fields=["code", "shakha"], name="unique_course_code_per_shakha"),
        ]

    def __str__(self):
        return f"{self.name} ({self.shakha.code})"


class Batch(AuditableModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="batches")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="batches")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    courses = models.ManyToManyField(VedicCourse, through="BatchCourse", related_name="batches")
    capacity = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-academic_year__starts_on", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "academic_year", "code"],
                name="unique_batch_code_per_branch_year",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class BatchCourse(AuditableModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="batch_courses")
    course = models.ForeignKey(VedicCourse, on_delete=models.PROTECT, related_name="batch_courses")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "course"], name="unique_course_per_batch"),
        ]
