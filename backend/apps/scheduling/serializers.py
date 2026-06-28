from rest_framework import serializers

from apps.scheduling.models import AcharyaBranchAssignment, AcharyaShakhaSpecialization, TeachingSession


class AcharyaShakhaSerializer(serializers.ModelSerializer):
    shakha_code = serializers.CharField(source="shakha.code", read_only=True)
    shakha_name = serializers.CharField(source="shakha.name", read_only=True)

    class Meta:
        model = AcharyaShakhaSpecialization
        fields = ["id", "shakha", "shakha_code", "shakha_name", "is_primary"]


class AcharyaBranchSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_timezone = serializers.CharField(source="branch.timezone", read_only=True)

    class Meta:
        model = AcharyaBranchAssignment
        fields = ["id", "branch", "branch_code", "branch_name", "branch_timezone", "is_primary"]


class TeachingSessionSerializer(serializers.ModelSerializer):
    acharya_email = serializers.EmailField(source="acharya.email", read_only=True)
    batch_name = serializers.CharField(source="batch.name", read_only=True)
    batch_code = serializers.CharField(source="batch.code", read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True, allow_null=True)

    class Meta:
        model = TeachingSession
        fields = [
            "id",
            "acharya",
            "acharya_email",
            "batch",
            "batch_name",
            "batch_code",
            "branch",
            "branch_code",
            "course",
            "course_name",
            "title",
            "starts_at",
            "ends_at",
            "timezone",
            "location",
            "status",
            "notes",
        ]


class TeachingSessionCreateSerializer(serializers.Serializer):
    acharya_id = serializers.UUIDField()
    batch_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    course_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=200)
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    timezone = serializers.CharField(max_length=50, default="Asia/Kolkata")
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class AcharyaRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)
    branch_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    shakha_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    profile = serializers.DictField(required=False)
    type_profile = serializers.DictField(required=False)


class AcharyaMappingSerializer(serializers.Serializer):
    acharya_id = serializers.UUIDField()
    branch_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    shakha_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
