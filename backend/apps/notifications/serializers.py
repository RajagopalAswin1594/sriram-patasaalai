from rest_framework import serializers

from apps.notifications.models import NotificationLog, NotificationTemplate


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = (
            "id",
            "code",
            "name",
            "channel",
            "subject_template",
            "body_template",
            "whatsapp_template_id",
            "is_active",
        )


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = (
            "id",
            "template_code",
            "channel",
            "recipient",
            "subject",
            "status",
            "error_message",
            "idempotency_key",
            "created_at",
        )


class NotificationTestSendSerializer(serializers.Serializer):
    template_code = serializers.CharField()
    recipient_email = serializers.EmailField(required=False, allow_blank=True)
    recipient_phone = serializers.CharField(required=False, allow_blank=True)
    context = serializers.DictField(required=False, default=dict)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)
