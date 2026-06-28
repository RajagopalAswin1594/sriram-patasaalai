from django.contrib import admin

from apps.audit.models import AuditLog, AuthenticationEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["occurred_at", "action", "entity_type", "entity_id", "actor"]
    list_filter = ["action", "entity_type"]
    search_fields = ["entity_repr", "entity_type"]
    readonly_fields = [field.name for field in AuditLog._meta.fields]


@admin.register(AuthenticationEvent)
class AuthenticationEventAdmin(admin.ModelAdmin):
    list_display = ["occurred_at", "event_type", "outcome", "user", "email_attempted"]
    list_filter = ["event_type", "outcome"]
    search_fields = ["email_attempted", "failure_reason"]
    readonly_fields = [field.name for field in AuthenticationEvent._meta.fields]
