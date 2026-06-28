from rest_framework import serializers

from apps.gurukulam_feedback.models import GurukulamFeedback, GurukulamFeedbackHistory


class GurukulamFeedbackSerializer(serializers.ModelSerializer):
    responded_by_email = serializers.CharField(source="responded_by.email", read_only=True, allow_null=True)

    class Meta:
        model = GurukulamFeedback
        fields = (
            "id",
            "feedback_number",
            "reporter_id",
            "reporter_email",
            "reporter_type",
            "is_anonymous",
            "branch_id",
            "category",
            "title",
            "description",
            "status",
            "admin_response",
            "responded_by_email",
            "responded_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "admin_response", "responded_by_email", "responded_at", "feedback_number")


class GurukulamFeedbackSubmitSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=[c[0] for c in GurukulamFeedback._meta.get_field("category").choices],
        required=False,
    )
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    reporter_email = serializers.EmailField(required=False, allow_blank=True)
    is_anonymous = serializers.BooleanField(default=False)


class GurukulamFeedbackStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)
    admin_response = serializers.CharField(required=False, allow_blank=True)


class GurukulamFeedbackHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(source="changed_by.email", read_only=True, allow_null=True)

    class Meta:
        model = GurukulamFeedbackHistory
        fields = ("from_status", "to_status", "changed_by_email", "reason", "occurred_at")
