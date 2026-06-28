from rest_framework import serializers

from apps.accounts.models import RelationshipType
from apps.students.models import BatchEnrollment, ParentChildLink, StudentBranchEnrollment


class StudentBranchEnrollmentSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_name = serializers.SerializerMethodField()
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    current_batch = serializers.SerializerMethodField()

    class Meta:
        model = StudentBranchEnrollment
        fields = [
            "id",
            "student",
            "student_email",
            "student_name",
            "branch",
            "branch_code",
            "status",
            "current_batch",
            "created_at",
        ]

    def get_student_name(self, obj):
        profile = getattr(obj.student, "profile", None)
        if profile:
            return profile.display_name or f"{profile.first_name} {profile.last_name}".strip()
        return obj.student.email

    def get_current_batch(self, obj):
        active = obj.batch_enrollments.filter(status="ACTIVE", is_deleted=False).select_related("batch").first()
        if not active:
            return None
        return {
            "id": str(active.batch.id),
            "code": active.batch.code,
            "name": active.batch.name,
            "effective_from": active.effective_from,
        }


class CreateStudentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)
    branch_id = serializers.UUIDField()
    batch_id = serializers.UUIDField(required=False)
    effective_from = serializers.DateField(required=False)
    profile = serializers.DictField(required=False)
    type_profile = serializers.DictField(required=False)


class BulkBatchAssignSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    student_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    effective_from = serializers.DateField(required=False)


class BatchTransferSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    from_batch_id = serializers.UUIDField()
    to_batch_id = serializers.UUIDField()
    effective_date = serializers.DateField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)


class ParentChildLinkSerializer(serializers.ModelSerializer):
    parent_email = serializers.EmailField(source="parent.email", read_only=True)
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ParentChildLink
        fields = [
            "id",
            "parent",
            "parent_email",
            "student",
            "student_email",
            "student_name",
            "relationship_type",
            "is_primary",
            "is_verified",
            "created_at",
        ]

    def get_student_name(self, obj):
        profile = getattr(obj.student, "profile", None)
        if profile:
            return profile.display_name or profile.first_name
        return obj.student.email


class ParentChildLinkCreateSerializer(serializers.Serializer):
    parent_id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    relationship_type = serializers.ChoiceField(choices=RelationshipType.choices, default=RelationshipType.GUARDIAN)
    is_primary = serializers.BooleanField(default=True)
    is_verified = serializers.BooleanField(default=True)
