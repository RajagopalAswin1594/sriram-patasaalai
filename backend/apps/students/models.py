from django.db import models

from apps.accounts.models import RelationshipType
from apps.core.models import AuditableModel


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"


class BatchEnrollmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    TRANSFERRED = "TRANSFERRED", "Transferred"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"


class StudentBranchEnrollment(AuditableModel):
    student = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="student_enrollments")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="student_enrollments")
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "branch"],
                condition=models.Q(status=EnrollmentStatus.ACTIVE, is_deleted=False),
                name="unique_active_student_branch_enrollment",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "status"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self):
        return f"{self.student.email} @ {self.branch.code}"


class BatchEnrollment(AuditableModel):
    student_enrollment = models.ForeignKey(
        StudentBranchEnrollment,
        on_delete=models.CASCADE,
        related_name="batch_enrollments",
    )
    batch = models.ForeignKey("academics.Batch", on_delete=models.PROTECT, related_name="enrollments")
    status = models.CharField(max_length=20, choices=BatchEnrollmentStatus.choices, default=BatchEnrollmentStatus.ACTIVE)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    transfer_reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["batch", "status"]),
            models.Index(fields=["student_enrollment", "status"]),
            models.Index(fields=["effective_from", "effective_to"]),
        ]

    def __str__(self):
        return f"{self.student_enrollment.student.email} → {self.batch.code}"


class ParentChildLink(AuditableModel):
    parent = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="child_links")
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="parent_links")
    relationship_type = models.CharField(max_length=20, choices=RelationshipType.choices, default=RelationshipType.GUARDIAN)
    is_primary = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["parent", "student"], name="unique_parent_child_link"),
        ]
        indexes = [
            models.Index(fields=["parent", "is_verified"]),
            models.Index(fields=["student", "is_verified"]),
        ]

    def __str__(self):
        return f"{self.parent.email} → {self.student.email}"
