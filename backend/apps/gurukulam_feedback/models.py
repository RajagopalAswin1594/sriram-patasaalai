import secrets

from django.db import models
from django.utils import timezone

from apps.core.models import AuditableModel


class GurukulamFeedbackCategory(models.TextChoices):
    TEACHING = "TEACHING", "Teaching & Curriculum"
    FACILITIES = "FACILITIES", "Facilities & Infrastructure"
    ADMINISTRATION = "ADMINISTRATION", "Administration & Communication"
    EVENTS = "EVENTS", "Events & Programs"
    HOSTEL = "HOSTEL", "Hostel & Mess"
    SUGGESTION = "SUGGESTION", "Suggestion"
    COMPLAINT = "COMPLAINT", "Complaint"
    APPRECIATION = "APPRECIATION", "Appreciation"


class GurukulamFeedbackStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    RESPONDED = "RESPONDED", "Responded"
    CLOSED = "CLOSED", "Closed"


def generate_gurukulam_feedback_number():
    year = timezone.now().year
    return f"GF-{year}-{secrets.token_hex(3).upper()}"


class GurukulamFeedback(AuditableModel):
    """General institutional feedback — not routed to GitHub or DevOps."""

    feedback_number = models.CharField(max_length=30, unique=True, default=generate_gurukulam_feedback_number)
    reporter = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gurukulam_feedback_submissions",
    )
    reporter_email = models.EmailField(blank=True)
    reporter_type = models.CharField(max_length=30, blank=True)
    is_anonymous = models.BooleanField(default=False)
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)

    category = models.CharField(
        max_length=30,
        choices=GurukulamFeedbackCategory.choices,
        default=GurukulamFeedbackCategory.SUGGESTION,
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=GurukulamFeedbackStatus.choices,
        default=GurukulamFeedbackStatus.SUBMITTED,
    )
    admin_response = models.TextField(blank=True)
    responded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gurukulam_feedback_responses",
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["category", "status"]),
        ]


class GurukulamFeedbackHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    feedback = models.ForeignKey(GurukulamFeedback, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name_plural = "gurukulam feedback histories"
