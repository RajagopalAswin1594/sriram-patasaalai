from django.db import models

from apps.core.models import AuditableModel


class AcharyaShakhaSpecialization(AuditableModel):
    acharya = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="acharya_shakhas")
    shakha = models.ForeignKey("academics.Shakha", on_delete=models.PROTECT, related_name="acharya_specializations")
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["acharya", "shakha"], name="unique_acharya_shakha"),
        ]

    def __str__(self):
        return f"{self.acharya.email} – {self.shakha.code}"


class AcharyaBranchAssignment(AuditableModel):
    acharya = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="acharya_branch_assignments")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="acharya_assignments")
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["acharya", "branch"], name="unique_acharya_branch"),
        ]

    def __str__(self):
        return f"{self.acharya.email} @ {self.branch.code}"


class SessionStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class TeachingSession(AuditableModel):
    acharya = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="teaching_sessions")
    batch = models.ForeignKey("academics.Batch", on_delete=models.PROTECT, related_name="teaching_sessions")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="teaching_sessions")
    course = models.ForeignKey(
        "academics.VedicCourse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_sessions",
    )
    title = models.CharField(max_length=200)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.SCHEDULED)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["acharya", "starts_at", "ends_at"]),
            models.Index(fields=["branch", "starts_at"]),
            models.Index(fields=["batch", "starts_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.starts_at})"
