from django.db import models

from apps.core.models import AuditableModel


class NotificationChannel(models.TextChoices):
    EMAIL = "EMAIL", "Email"
    SMS = "SMS", "SMS"
    WHATSAPP = "WHATSAPP", "WhatsApp"


class NotificationDeliveryStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"
    SKIPPED = "SKIPPED", "Skipped"


class NotificationTemplate(AuditableModel):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    subject_template = models.CharField(max_length=255, blank=True)
    body_template = models.TextField()
    whatsapp_template_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(fields=["code", "channel"], name="unique_template_code_channel"),
        ]

    def __str__(self):
        return f"{self.code} ({self.channel})"


class NotificationLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    template_code = models.CharField(max_length=50, db_index=True)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=NotificationDeliveryStatus.choices)
    error_message = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["idempotency_key", "channel"],
                condition=models.Q(idempotency_key__gt=""),
                name="unique_notification_idempotency_per_channel",
            ),
        ]
