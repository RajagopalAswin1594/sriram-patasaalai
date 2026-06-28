from rest_framework import serializers

from apps.curriculum.models import CourseModule, Lesson, LessonResource, SyllabusVersion


class LessonResourceSerializer(serializers.ModelSerializer):
    stream_url = serializers.SerializerMethodField()

    class Meta:
        model = LessonResource
        fields = [
            "id",
            "resource_type",
            "title",
            "file_name",
            "content_type",
            "file_size",
            "duration_seconds",
            "text_body",
            "stream_url",
        ]

    def get_stream_url(self, obj):
        if not obj.s3_key:
            return None
        from apps.core.media_storage import MediaStorageService

        return MediaStorageService.get_stream_url(
            obj.s3_bucket, obj.s3_key, obj.content_type, obj.file_name or "media"
        )


class LessonSerializer(serializers.ModelSerializer):
    resources = LessonResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "title_sa",
            "title_ta",
            "content_text",
            "sort_order",
            "estimated_minutes",
            "resources",
        ]


class CourseModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = CourseModule
        fields = ["id", "title", "title_sa", "title_ta", "description", "sort_order", "lessons"]


class SyllabusVersionSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    modules = CourseModuleSerializer(many=True, read_only=True)

    class Meta:
        model = SyllabusVersion
        fields = [
            "id",
            "course",
            "course_code",
            "course_name",
            "version_label",
            "version_number",
            "status",
            "published_at",
            "notes",
            "modules",
            "created_at",
        ]


class SyllabusCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    version_label = serializers.CharField(max_length=30)
    notes = serializers.CharField(required=False, allow_blank=True)
    fork_from_id = serializers.UUIDField(required=False)


class ModuleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = ["syllabus", "title", "title_sa", "title_ta", "description", "sort_order"]


class LessonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["module", "title", "title_sa", "title_ta", "content_text", "sort_order", "estimated_minutes"]


class ResourcePresignSerializer(serializers.Serializer):
    lesson_id = serializers.UUIDField()
    resource_type = serializers.ChoiceField(choices=["PDF", "VIDEO", "AUDIO"])
    file_name = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(min_value=1)
    title = serializers.CharField(max_length=255)


class ResourceConfirmSerializer(serializers.Serializer):
    resource_id = serializers.UUIDField()
    duration_seconds = serializers.IntegerField(required=False, min_value=0)


class TextResourceSerializer(serializers.Serializer):
    lesson_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    text_body = serializers.CharField()
