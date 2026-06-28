from rest_framework import serializers

from apps.audit.models import AuditLog, AuthenticationEvent


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, allow_null=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_id",
            "actor_email",
            "action",
            "entity_type",
            "entity_id",
            "entity_repr",
            "branch_id",
            "branch_code",
            "changes",
            "metadata",
            "ip_address",
            "user_agent",
            "correlation_id",
            "occurred_at",
        ]


class AuthenticationEventSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True, allow_null=True)

    class Meta:
        model = AuthenticationEvent
        fields = [
            "id",
            "user_id",
            "user_email",
            "event_type",
            "outcome",
            "failure_reason",
            "email_attempted",
            "refresh_token_jti",
            "branch_id",
            "branch_code",
            "ip_address",
            "user_agent",
            "device_fingerprint",
            "geo_country",
            "metadata",
            "occurred_at",
        ]
