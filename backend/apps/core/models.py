import uuid

from django.db import models
from django.utils import timezone

from apps.core.context import get_audit_context


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AuditableModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated",
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_deleted",
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        ctx = get_audit_context()
        actor = ctx.get("actor")
        if self._state.adding and actor and not self.created_by_id:
            self.created_by = actor
        if actor:
            self.updated_by = actor
        super().save(*args, **kwargs)

    def soft_delete(self, actor=None):
        ctx = get_audit_context()
        actor = actor or ctx.get("actor")
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = actor
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at", "updated_by"])

    def restore(self, actor=None):
        ctx = get_audit_context()
        actor = actor or ctx.get("actor")
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        if actor:
            self.updated_by = actor
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at", "updated_by"])
