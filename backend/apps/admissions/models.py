import secrets
import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import AuditableModel


class ApplicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Payment Pending"
    PENDING = "PENDING", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    # Deprecated — use PENDING
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review (Legacy)"


class DocumentType(models.TextChoices):
    STUDENT_PHOTO = "STUDENT_PHOTO", "Student Photo"
    BIRTH_CERTIFICATE = "BIRTH_CERTIFICATE", "Birth Certificate"
    PREVIOUS_SCHOOL_RECORD = "PREVIOUS_SCHOOL_RECORD", "Previous School Record"
    AADHAAR = "AADHAAR", "Aadhaar Card"
    OTHER = "OTHER", "Other Document"


class DocumentUploadStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Upload"
    UPLOADED = "UPLOADED", "Uploaded"
    VERIFIED = "VERIFIED", "Verified"
    REJECTED = "REJECTED", "Rejected"
    RESUBMIT_REQUESTED = "RESUBMIT_REQUESTED", "Resubmit Requested"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    INITIATED = "INITIATED", "Initiated"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class PaymentGateway(models.TextChoices):
    RAZORPAY = "RAZORPAY", "Razorpay"
    DEMO = "DEMO", "Demo (Development)"


def generate_application_number():
    year = timezone.now().year
    suffix = secrets.token_hex(3).upper()
    return f"APP-{year}-{suffix}"


def generate_access_token():
    return secrets.token_urlsafe(32)


class AdmissionApplication(AuditableModel):
    application_number = models.CharField(max_length=30, unique=True, default=generate_application_number)
    access_token = models.CharField(max_length=64, unique=True, default=generate_access_token)
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="applications")
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        db_index=True,
    )

    student_first_name = models.CharField(max_length=150)
    student_last_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, blank=True)
    previous_school = models.CharField(max_length=200, blank=True)
    grade_applying = models.CharField(max_length=50)

    parent_name = models.CharField(max_length=200)
    parent_phone = models.CharField(max_length=20)
    parent_email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=30, default="GUARDIAN")

    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default="IN")

    preferred_language = models.CharField(max_length=10, default="en")
    application_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("500.00"))
    notes = models.TextField(blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_applications",
    )
    rejection_reason = models.TextField(blank=True)
    review_notes = models.TextField(blank=True, help_text="Internal admin notes; not shared with applicant.")
    assigned_to = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_applications",
    )
    provisioned_student = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="provisioned_from_application",
    )
    data_consent_at = models.DateTimeField(null=True, blank=True)
    data_consent_version = models.CharField(max_length=20, blank=True, default="v1.0")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "branch"]),
            models.Index(fields=["parent_phone"]),
            models.Index(fields=["application_number"]),
        ]

    def __str__(self):
        return f"{self.application_number} – {self.student_first_name}"


class ApplicationDocument(AuditableModel):
    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    content_type = models.CharField(max_length=100, blank=True)
    s3_bucket = models.CharField(max_length=100, blank=True)
    s3_key = models.CharField(max_length=500, blank=True)
    upload_status = models.CharField(
        max_length=20,
        choices=DocumentUploadStatus.choices,
        default=DocumentUploadStatus.PENDING,
    )
    uploaded_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="Reason shared with applicant for reject/resubmit.")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_application_documents",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "document_type"],
                name="unique_application_document_type",
            ),
        ]

    def __str__(self):
        return f"{self.application.application_number} – {self.document_type}"


class ApplicationPayment(AuditableModel):
    application = models.OneToOneField(AdmissionApplication, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    gateway = models.CharField(max_length=20, choices=PaymentGateway.choices, default=PaymentGateway.RAZORPAY)
    gateway_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    def __str__(self):
        return f"Payment for {self.application.application_number}"


class NotificationChannel(models.TextChoices):
    EMAIL = "EMAIL", "Email"
    SMS = "SMS", "SMS"
    WHATSAPP = "WHATSAPP", "WhatsApp"


class NotificationEventType(models.TextChoices):
    APPLICATION_PENDING = "APPLICATION_PENDING", "Application Pending Review"
    APPLICATION_APPROVED = "APPLICATION_APPROVED", "Application Approved"
    APPLICATION_REJECTED = "APPLICATION_REJECTED", "Application Rejected"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Payment Confirmed"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED", "Document Verified"
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED", "Document Rejected"
    DOCUMENT_RESUBMIT_REQUESTED = "DOCUMENT_RESUBMIT_REQUESTED", "Document Resubmit Requested"


class NotificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"


class ApplicationStatusHistory(models.Model):
    """Append-only status transition log — prevents stuck applications without audit trail."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="application_status_changes",
    )
    reason = models.TextField(blank=True)
    metadata = models.JSONField(null=True, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name_plural = "application status histories"


class ApplicationNotification(models.Model):
    """Audit log of all outbound notifications (email/WhatsApp)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    event_type = models.CharField(max_length=30, choices=NotificationEventType.choices)
    recipient = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ApplicationDocumentReviewLog(models.Model):
    """Append-only audit log for per-document review actions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(ApplicationDocument, on_delete=models.CASCADE, related_name="review_logs")
    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name="document_review_logs")
    action = models.CharField(max_length=30)
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="document_review_actions",
    )
    reason = models.TextField(blank=True)
    notified_channels = models.JSONField(default=list, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
