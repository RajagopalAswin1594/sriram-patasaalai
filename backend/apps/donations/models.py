import secrets

from django.db import models
from django.utils import timezone

from apps.core.models import AuditableModel


class DonationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    INITIATED = "INITIATED", "Initiated"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


def generate_donation_number():
    year = timezone.now().year
    return f"DON-{year}-{secrets.token_hex(3).upper()}"


class DonationCategory(AuditableModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Donation(AuditableModel):
    donation_number = models.CharField(max_length=30, unique=True, default=generate_donation_number)
    category = models.ForeignKey(DonationCategory, on_delete=models.PROTECT, related_name="donations")
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)
    sponsored_student = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sponsorships",
    )
    sponsored_acharya = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acharya_sponsorships",
    )
    donor_name = models.CharField(max_length=200)
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=20, choices=DonationStatus.choices, default=DonationStatus.PENDING)
    gateway_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True, db_index=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    webhook_event_id = models.CharField(max_length=100, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=64, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["branch", "status"]),
        ]


class DonationReceipt(AuditableModel):
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=40, unique=True)
    registration_12a = models.CharField(max_length=100, blank=True)
    registration_80g = models.CharField(max_length=100, blank=True)
    pdf_s3_bucket = models.CharField(max_length=100, blank=True)
    pdf_s3_key = models.CharField(max_length=500, blank=True)
    emailed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.receipt_number
