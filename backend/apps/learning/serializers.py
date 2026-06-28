from rest_framework import serializers

from apps.learning.models import AttendanceRecord, AttendanceSession, Exam, ExamScore, PracticeSubmission, Transcript


class PracticeSubmissionSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)
    stream_url = serializers.SerializerMethodField()

    class Meta:
        model = PracticeSubmission
        fields = [
            "id",
            "student",
            "student_email",
            "batch",
            "lesson",
            "title",
            "file_name",
            "content_type",
            "duration_seconds",
            "status",
            "acharya_feedback",
            "oral_grade",
            "reviewed_at",
            "stream_url",
            "created_at",
        ]

    def get_stream_url(self, obj):
        if not obj.s3_key:
            return None
        from apps.core.media_storage import MediaStorageService

        return MediaStorageService.get_stream_url(obj.s3_bucket, obj.s3_key, obj.content_type, obj.file_name)


class PracticeReviewSerializer(serializers.Serializer):
    feedback = serializers.CharField()
    oral_grade = serializers.CharField(required=False, allow_blank=True)


class PracticePresignSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    lesson_id = serializers.UUIDField(required=False)
    title = serializers.CharField(max_length=200)
    file_name = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(min_value=1)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ["id", "student", "student_email", "status", "latitude", "longitude", "marked_offline"]


class AttendanceSessionSerializer(serializers.ModelSerializer):
    records = AttendanceRecordSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceSession
        fields = ["id", "batch", "session_date", "acharya", "notes", "records"]


class AttendanceMarkSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    session_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True)
    records = serializers.ListField(child=serializers.DictField())


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["id", "batch", "course", "title", "exam_type", "scheduled_at", "max_score", "acharya"]


class ExamScoreSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)

    class Meta:
        model = ExamScore
        fields = ["id", "exam", "student", "student_email", "score", "oral_grade", "notes", "revision"]


class ExamScoreWriteSerializer(serializers.Serializer):
    exam_id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    score = serializers.DecimalField(max_digits=6, decimal_places=2)
    oral_grade = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = ["id", "student", "batch", "grades", "generated_at"]
