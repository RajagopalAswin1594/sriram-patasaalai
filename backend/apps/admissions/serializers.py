from rest_framework import serializers

from apps.admissions.models import (
    AdmissionApplication,
    ApplicationDocument,
    ApplicationNotification,
    ApplicationPayment,
    ApplicationStatus,
    ApplicationStatusHistory,
    DocumentType,
    NotificationChannel,
)
from apps.admissions.privacy import PrivacyMaskingService


class PublicBranchSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    city = serializers.CharField()


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True, allow_null=True)

    class Meta:
        model = ApplicationDocument
        fields = [
            "id",
            "document_type",
            "file_name",
            "file_size",
            "content_type",
            "upload_status",
            "uploaded_at",
            "review_notes",
            "reviewed_at",
            "reviewed_by_email",
        ]


class ApplicationPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationPayment
        fields = ["id", "amount", "currency", "status", "gateway", "paid_at"]


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True, allow_null=True)

    class Meta:
        model = ApplicationStatusHistory
        fields = ["id", "from_status", "to_status", "changed_by_email", "reason", "metadata", "occurred_at"]


class ApplicationNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationNotification
        fields = ["id", "channel", "event_type", "recipient", "status", "sent_at", "created_at", "error_message"]


class AdmissionApplicationSerializer(serializers.ModelSerializer):
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    payment = ApplicationPaymentSerializer(read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True, allow_null=True)
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, allow_null=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)
    notifications = ApplicationNotificationSerializer(many=True, read_only=True)

    class Meta:
        model = AdmissionApplication
        fields = [
            "id",
            "application_number",
            "access_token",
            "branch",
            "branch_code",
            "branch_name",
            "status",
            "student_first_name",
            "student_last_name",
            "date_of_birth",
            "gender",
            "previous_school",
            "grade_applying",
            "parent_name",
            "parent_phone",
            "parent_email",
            "relationship",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "preferred_language",
            "application_fee_amount",
            "submitted_at",
            "reviewed_at",
            "reviewed_by_email",
            "assigned_to_email",
            "rejection_reason",
            "review_notes",
            "data_consent_at",
            "data_consent_version",
            "documents",
            "payment",
            "status_history",
            "notifications",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "application_number",
            "access_token",
            "status",
            "submitted_at",
            "reviewed_at",
            "rejection_reason",
            "data_consent_at",
            "data_consent_version",
            "created_at",
        ]


class AdminApplicationListSerializer(AdmissionApplicationSerializer):
    """List view with optional PII masking for GDPR-aligned access control."""

    pii_masked = serializers.BooleanField(read_only=True, default=False)

    class Meta(AdmissionApplicationSerializer.Meta):
        fields = AdmissionApplicationSerializer.Meta.fields + ["pii_masked"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        reveal = user and PrivacyMaskingService.user_can_view_full_pii(user)
        return PrivacyMaskingService.mask_application_data(data, reveal=reveal)


class PublicApplicationCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    student_first_name = serializers.CharField(max_length=150)
    student_last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    date_of_birth = serializers.DateField()
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    previous_school = serializers.CharField(max_length=200, required=False, allow_blank=True)
    grade_applying = serializers.CharField(max_length=50)
    parent_name = serializers.CharField(max_length=200)
    parent_phone = serializers.CharField(max_length=20)
    parent_email = serializers.EmailField(required=False, allow_blank=True)
    relationship = serializers.CharField(max_length=30, default="GUARDIAN")
    address_line_1 = serializers.CharField(max_length=255)
    address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2, default="IN")
    preferred_language = serializers.CharField(max_length=10, default="en")
    data_consent = serializers.BooleanField()

    def validate_data_consent(self, value):
        if not value:
            raise serializers.ValidationError("You must consent to data processing to apply.")
        return value


class PublicApplicationUpdateSerializer(serializers.Serializer):
    student_first_name = serializers.CharField(max_length=150, required=False)
    student_last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    previous_school = serializers.CharField(max_length=200, required=False, allow_blank=True)
    grade_applying = serializers.CharField(max_length=50, required=False)
    parent_name = serializers.CharField(max_length=200, required=False)
    parent_phone = serializers.CharField(max_length=20, required=False)
    parent_email = serializers.EmailField(required=False, allow_blank=True)
    relationship = serializers.CharField(max_length=30, required=False)
    address_line_1 = serializers.CharField(max_length=255, required=False)
    address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=100, required=False)
    postal_code = serializers.CharField(max_length=20, required=False)
    preferred_language = serializers.CharField(max_length=10, required=False)


class DocumentPresignSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    document_type = serializers.ChoiceField(choices=DocumentType.choices)
    file_name = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(min_value=1)


class DocumentConfirmSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    document_id = serializers.UUIDField()


class PaymentConfirmSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    order_id = serializers.CharField(required=False)
    payment_id = serializers.CharField(required=False)
    signature = serializers.CharField(required=False)


class ApplicationReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[ApplicationStatus.APPROVED, ApplicationStatus.REJECTED])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    review_notes = serializers.CharField(required=False, allow_blank=True)


class ApplicationAssignSerializer(serializers.Serializer):
    assigned_to_id = serializers.UUIDField()


class DocumentReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT", "REQUEST_RESUBMIT"])
    reason = serializers.CharField(required=False, allow_blank=True)
    notify_channels = serializers.ListField(
        child=serializers.ChoiceField(choices=NotificationChannel.choices),
        required=False,
        allow_empty=False,
    )
