import uuid

from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    RESTORE = "RESTORE", "Restore"
    STATUS_CHANGE = "STATUS_CHANGE", "Status Change"


class AuthEventType(models.TextChoices):
    LOGIN_ATTEMPT = "LOGIN_ATTEMPT", "Login Attempt"
    LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login Success"
    LOGOUT = "LOGOUT", "Logout"
    TOKEN_REFRESH = "TOKEN_REFRESH", "Token Refresh"
    TOKEN_REVOKE = "TOKEN_REVOKE", "Token Revoke"
    PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST", "Password Reset Request"
    PASSWORD_RESET_COMPLETE = "PASSWORD_RESET_COMPLETE", "Password Reset Complete"
    PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED", "Account Locked"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED", "Account Unlocked"
    ACCOUNT_STATUS_CHANGE = "ACCOUNT_STATUS_CHANGE", "Account Status Change"


class AuthEventOutcome(models.TextChoices):
    SUCCESS = "SUCCESS", "Success"
    FAILURE = "FAILURE", "Failure"
    BLOCKED = "BLOCKED", "Blocked"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    entity_repr = models.CharField(max_length=500, blank=True)
    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    changes = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    correlation_id = models.UUIDField(null=True, blank=True, db_index=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]


class AuthenticationEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authentication_events",
    )
    event_type = models.CharField(max_length=40, choices=AuthEventType.choices, db_index=True)
    outcome = models.CharField(max_length=20, choices=AuthEventOutcome.choices)
    failure_reason = models.CharField(max_length=50, blank=True)
    email_attempted = models.CharField(max_length=255, blank=True)
    refresh_token_jti = models.UUIDField(null=True, blank=True)
    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authentication_events",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    geo_country = models.CharField(max_length=2, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
