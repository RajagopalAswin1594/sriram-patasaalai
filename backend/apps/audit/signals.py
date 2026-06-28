from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.audit.models import AuditAction
from apps.audit.services import build_changes, record_audit


def _is_audited(sender):
    from django.conf import settings

    label = f"{sender._meta.app_label}.{sender._meta.model_name}"
    return label in settings.AUDITED_MODELS


@receiver(pre_save)
def capture_pre_save_state(sender, instance, **kwargs):
    if not _is_audited(sender):
        return
    if instance.pk:
        instance._audit_previous = sender.all_objects.filter(pk=instance.pk).first()


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not _is_audited(sender):
        return
    if created:
        record_audit(instance, AuditAction.CREATE)
        return

    previous = getattr(instance, "_audit_previous", None)
    if previous and getattr(previous, "is_deleted", False) is True and not instance.is_deleted:
        record_audit(instance, AuditAction.RESTORE, changes=build_changes(instance, previous=previous))
        return

    changes = build_changes(instance, previous=previous)
    if changes:
        record_audit(instance, AuditAction.UPDATE, changes=changes)
