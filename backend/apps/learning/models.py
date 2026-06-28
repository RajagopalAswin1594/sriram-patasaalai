from django.db import models

from apps.core.models import AuditableModel


class PracticeStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    REVIEWED = "REVIEWED", "Reviewed"


class AttendanceStatus(models.TextChoices):
    PRESENT = "PRESENT", "Present"
    ABSENT = "ABSENT", "Absent"
    LATE = "LATE", "Late"
    EXCUSED = "EXCUSED", "Excused"


class ExamType(models.TextChoices):
    ORAL = "ORAL", "Oral"
    WRITTEN = "WRITTEN", "Written"


class PracticeSubmission(AuditableModel):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="practice_submissions")
    batch = models.ForeignKey("academics.Batch", on_delete=models.PROTECT, related_name="practice_submissions")
    lesson = models.ForeignKey("curriculum.Lesson", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField(default=0)
    s3_bucket = models.CharField(max_length=100, blank=True)
    s3_key = models.CharField(max_length=500, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PracticeStatus.choices, default=PracticeStatus.SUBMITTED)
    acharya_feedback = models.TextField(blank=True)
    oral_grade = models.CharField(max_length=50, blank=True, help_text="Traditional oral grading scale")
    reviewed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="practice_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class AttendanceSession(AuditableModel):
    batch = models.ForeignKey("academics.Batch", on_delete=models.PROTECT, related_name="attendance_sessions")
    session_date = models.DateField(db_index=True)
    acharya = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="attendance_sessions_marked")
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "session_date"], name="unique_attendance_session_per_batch_day"),
        ]


class AttendanceRecord(AuditableModel):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    marked_offline = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "student"], name="unique_attendance_per_student_session"),
        ]


class Exam(AuditableModel):
    batch = models.ForeignKey("academics.Batch", on_delete=models.PROTECT, related_name="exams")
    course = models.ForeignKey("academics.VedicCourse", on_delete=models.PROTECT, related_name="exams")
    title = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=ExamType.choices, default=ExamType.ORAL)
    scheduled_at = models.DateTimeField()
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    acharya = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="exams_scheduled")

    class Meta:
        ordering = ["scheduled_at"]


class ExamScore(AuditableModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="scores")
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="exam_scores")
    score = models.DecimalField(max_digits=6, decimal_places=2)
    oral_grade = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=1)
    entered_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="exam_scores_entered")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["exam", "student"], name="unique_exam_score_per_student"),
        ]


class ExamScoreRevision(models.Model):
    """Append-only revision log to prevent silent grade overwrites."""

    id = models.BigAutoField(primary_key=True)
    exam_score = models.ForeignKey(ExamScore, on_delete=models.CASCADE, related_name="revisions")
    previous_score = models.DecimalField(max_digits=6, decimal_places=2)
    new_score = models.DecimalField(max_digits=6, decimal_places=2)
    previous_oral_grade = models.CharField(max_length=50, blank=True)
    new_oral_grade = models.CharField(max_length=50, blank=True)
    changed_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    reason = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)


class Transcript(AuditableModel):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="transcripts")
    batch = models.ForeignKey("academics.Batch", on_delete=models.PROTECT, related_name="transcripts")
    grades = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "batch"], name="unique_transcript_per_student_batch"),
        ]
