from rest_framework import serializers

from apps.certifications.models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            "id",
            "certificate_number",
            "verification_code",
            "student_name",
            "course_name",
            "branch_name",
            "issued_at",
            "status",
            "pdf_url",
        ]

    def get_pdf_url(self, obj):
        if not obj.pdf_s3_key:
            return None
        from apps.core.media_storage import MediaStorageService

        return MediaStorageService.get_stream_url(
            obj.pdf_s3_bucket, obj.pdf_s3_key, "application/pdf", f"{obj.certificate_number}.pdf"
        )


class CertificateIssueSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    batch_id = serializers.UUIDField()


class CertificateVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            "certificate_number",
            "student_name",
            "course_name",
            "branch_name",
            "issued_at",
            "status",
        ]
