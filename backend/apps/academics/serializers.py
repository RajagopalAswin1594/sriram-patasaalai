from rest_framework import serializers

from apps.academics.models import AcademicYear, Batch, BatchCourse, Shakha, VedicCourse


class ShakhaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shakha
        fields = ["id", "code", "name", "description"]


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ["id", "name", "starts_on", "ends_on", "is_current"]


class VedicCourseSerializer(serializers.ModelSerializer):
    shakha_code = serializers.CharField(source="shakha.code", read_only=True)
    shakha_name = serializers.CharField(source="shakha.name", read_only=True)

    class Meta:
        model = VedicCourse
        fields = ["id", "code", "name", "shakha", "shakha_code", "shakha_name", "grade_level", "description"]


class BatchSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)
    course_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    courses = VedicCourseSerializer(many=True, read_only=True)
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = [
            "id",
            "branch",
            "branch_code",
            "branch_name",
            "academic_year",
            "academic_year_name",
            "code",
            "name",
            "capacity",
            "is_active",
            "course_ids",
            "courses",
            "enrolled_count",
        ]

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status="ACTIVE", is_deleted=False).count()

    def create(self, validated_data):
        course_ids = validated_data.pop("course_ids", [])
        batch = Batch.objects.create(**validated_data)
        for course_id in course_ids:
            BatchCourse.objects.get_or_create(batch=batch, course_id=course_id)
        return batch

    def update(self, instance, validated_data):
        course_ids = validated_data.pop("course_ids", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if course_ids is not None:
            BatchCourse.objects.filter(batch=instance).delete()
            for course_id in course_ids:
                BatchCourse.objects.get_or_create(batch=instance, course_id=course_id)
        return instance
