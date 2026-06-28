import uuid

from apps.audit.models import AuditAction, AuditLog, AuthenticationEvent, AuthEventOutcome, AuthEventType
from apps.core.context import get_audit_context, get_correlation_id


def _serialize_value(value):
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def build_changes(instance, previous=None, update_fields=None):
    if previous is None:
        return None
    changes = {}
    for field in instance._meta.concrete_fields:
        if field.is_relation and field.many_to_many:
            continue
        if update_fields and field.name not in update_fields:
            continue
        old_value = getattr(previous, field.attname, None)
        new_value = getattr(instance, field.attname, None)
        if old_value != new_value:
            changes[field.name] = {
                "old": _serialize_value(old_value),
                "new": _serialize_value(new_value),
            }
    return changes or None


def record_audit(instance, action, changes=None):
    from django.conf import settings

    ctx = get_audit_context()
    sensitive = settings.SENSITIVE_AUDIT_FIELDS
    if changes:
        changes = {
            key: value
            for key, value in changes.items()
            if key not in sensitive
        }

    AuditLog.objects.create(
        actor=ctx.get("actor"),
        action=action,
        entity_type=f"{instance._meta.app_label}.{instance._meta.model_name}",
        entity_id=instance.pk,
        entity_repr=str(instance)[:500],
        branch=ctx.get("branch"),
        changes=changes,
        metadata=ctx.get("metadata"),
        ip_address=ctx.get("ip_address"),
        user_agent=ctx.get("user_agent", ""),
        correlation_id=get_correlation_id(),
    )


def record_auth_event(
    *,
    event_type,
    outcome,
    user=None,
    failure_reason="",
    email_attempted="",
    refresh_token_jti=None,
    branch_id=None,
    ip_address=None,
    user_agent="",
    device_fingerprint="",
    metadata=None,
):
    branch = None
    if branch_id:
        from apps.branches.models import Branch

        branch = Branch.objects.filter(id=branch_id).first()

    AuthenticationEvent.objects.create(
        user=user,
        event_type=event_type,
        outcome=outcome,
        failure_reason=failure_reason or "",
        email_attempted=email_attempted or "",
        refresh_token_jti=refresh_token_jti,
        branch=branch,
        ip_address=ip_address,
        user_agent=user_agent or "",
        device_fingerprint=device_fingerprint or "",
        metadata=metadata,
    )
