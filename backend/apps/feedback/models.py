import secrets

from django.db import models
from django.utils import timezone

from apps.core.models import AuditableModel


class FeedbackCategory(models.TextChoices):
    BUG = "BUG", "Bug Report"
    FEATURE = "FEATURE", "Feature Request"
    IMPROVEMENT = "IMPROVEMENT", "Improvement Suggestion"
    PERFORMANCE = "PERFORMANCE", "Performance Issue"
    UI_UX = "UI_UX", "UI/UX Issue"
    SECURITY = "SECURITY", "Security Concern"
    CONTENT = "CONTENT", "Content Correction"
    COURSE = "COURSE", "Course Feedback"
    ACHARYA = "ACHARYA", "Acharya Feedback"
    COMPLAINT = "COMPLAINT", "Complaint"
    APPRECIATION = "APPRECIATION", "Appreciation"


class FeedbackModule(models.TextChoices):
    ADMISSIONS = "ADMISSIONS", "Admissions"
    STUDENTS = "STUDENTS", "Students"
    LMS = "LMS", "Learning / LMS"
    ATTENDANCE = "ATTENDANCE", "Attendance"
    CURRICULUM = "CURRICULUM", "Curriculum"
    HOSTEL = "HOSTEL", "Hostel"
    DONATIONS = "DONATIONS", "Donations"
    COMMUNITY = "COMMUNITY", "Community"
    ALUMNI = "ALUMNI", "Alumni"
    MOBILE = "MOBILE", "Mobile App"
    PLATFORM = "PLATFORM", "Platform / General"


class FeedbackEnvironment(models.TextChoices):
    LOCAL = "LOCAL", "Local"
    DEV = "DEV", "Development"
    QA = "QA", "QA"
    UAT = "UAT", "UAT"
    PRODUCTION = "PRODUCTION", "Production"


class FeedbackPlatform(models.TextChoices):
    WEB = "WEB", "Web"
    ANDROID = "ANDROID", "Android"
    IOS = "IOS", "iOS"


class FeedbackStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    AI_ANALYZED = "AI_ANALYZED", "AI Analyzed"
    DUPLICATE_LINKED = "DUPLICATE_LINKED", "Linked to Duplicate"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Manual Approval"
    GITHUB_CREATED = "GITHUB_CREATED", "GitHub Issue Created"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    TESTING = "TESTING", "Testing"
    RELEASED = "RELEASED", "Released"
    CLOSED = "CLOSED", "Closed"


class FeedbackSeverity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class FeedbackPriority(models.TextChoices):
    P4 = "P4", "P4 – Low"
    P3 = "P3", "P3 – Normal"
    P2 = "P2", "P2 – High"
    P1 = "P1", "P1 – Urgent"


def generate_feedback_number():
    year = timezone.now().year
    return f"FB-{year}-{secrets.token_hex(3).upper()}"


class Feedback(AuditableModel):
    feedback_number = models.CharField(max_length=30, unique=True, default=generate_feedback_number)
    reporter = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_submissions",
    )
    reporter_email = models.EmailField(blank=True)
    reporter_type = models.CharField(max_length=30, blank=True)
    is_anonymous = models.BooleanField(default=False)
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)

    category = models.CharField(max_length=30, choices=FeedbackCategory.choices, default=FeedbackCategory.BUG)
    source_module = models.CharField(max_length=30, choices=FeedbackModule.choices, default=FeedbackModule.PLATFORM)
    environment = models.CharField(max_length=20, choices=FeedbackEnvironment.choices, default=FeedbackEnvironment.PRODUCTION)
    platform = models.CharField(max_length=20, choices=FeedbackPlatform.choices, default=FeedbackPlatform.WEB)
    app_version = models.CharField(max_length=30, blank=True)
    browser_device = models.CharField(max_length=255, blank=True)
    screen_name = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    steps_to_reproduce = models.TextField(blank=True)
    expected_result = models.TextField(blank=True)
    actual_result = models.TextField(blank=True)

    status = models.CharField(max_length=30, choices=FeedbackStatus.choices, default=FeedbackStatus.SUBMITTED)
    severity = models.CharField(max_length=20, choices=FeedbackSeverity.choices, default=FeedbackSeverity.MEDIUM)
    priority = models.CharField(max_length=5, choices=FeedbackPriority.choices, default=FeedbackPriority.P3)
    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicates",
    )
    assigned_team = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["source_module", "status"]),
            models.Index(fields=["environment", "priority"]),
        ]


class FeedbackAttachment(AuditableModel):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name="attachments")
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    s3_bucket = models.CharField(max_length=100, blank=True)
    s3_key = models.CharField(max_length=500, blank=True)
    is_screenshot = models.BooleanField(default=False)


class FeedbackAnalysis(AuditableModel):
    feedback = models.OneToOneField(Feedback, on_delete=models.CASCADE, related_name="analysis")
    sentiment = models.CharField(max_length=20, blank=True)
    ai_category = models.CharField(max_length=30, blank=True)
    ai_summary = models.TextField(blank=True)
    root_cause_suggestion = models.TextField(blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recommended_priority = models.CharField(max_length=5, blank=True)
    recommended_team = models.CharField(max_length=100, blank=True)
    create_github_issue = models.BooleanField(default=False)
    github_issue_draft = models.TextField(blank=True)
    raw_analysis = models.JSONField(default=dict)


class FeedbackHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name_plural = "feedback histories"


class FeedbackComment(AuditableModel):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    body = models.TextField()
    is_internal = models.BooleanField(default=True)


class GitHubIssueMapping(AuditableModel):
    class SyncMode(models.TextChoices):
        STUB = "STUB", "Demo / stub (not in GitHub)"
        REAL = "REAL", "Created in GitHub"
        FAILED = "FAILED", "GitHub API failed"

    feedback = models.OneToOneField(Feedback, on_delete=models.CASCADE, related_name="github_issue")
    issue_number = models.PositiveIntegerField(db_index=True)
    issue_url = models.URLField(max_length=500)
    repo = models.CharField(max_length=200)
    labels = models.JSONField(default=list, blank=True)
    state = models.CharField(max_length=30, default="open")
    created_by_system = models.BooleanField(default=True)
    sync_mode = models.CharField(max_length=10, choices=SyncMode.choices, default=SyncMode.STUB)
    http_status = models.PositiveIntegerField(null=True, blank=True)
    api_error = models.TextField(blank=True)
    branch_name = models.CharField(max_length=200, blank=True)
    milestone = models.CharField(max_length=100, blank=True)
    project_node_id = models.CharField(max_length=100, blank=True)
