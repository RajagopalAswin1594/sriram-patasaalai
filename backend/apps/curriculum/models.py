from django.db import models

from apps.core.models import AuditableModel


class SyllabusStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"


class ResourceType(models.TextChoices):
    PDF = "PDF", "PDF"
    TEXT = "TEXT", "Text"
    VIDEO = "VIDEO", "Video"
    AUDIO = "AUDIO", "Audio"


class SyllabusVersion(AuditableModel):
    """Versioned syllabus per Vedic course — flat module/lesson tree for query performance."""

    course = models.ForeignKey("academics.VedicCourse", on_delete=models.CASCADE, related_name="syllabus_versions")
    version_label = models.CharField(max_length=30)
    version_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=SyllabusStatus.choices, default=SyllabusStatus.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(fields=["course", "version_number"], name="unique_syllabus_version_per_course"),
        ]

    def __str__(self):
        return f"{self.course.code} – {self.version_label}"


class CourseModule(AuditableModel):
    syllabus = models.ForeignKey(SyllabusVersion, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    title_sa = models.CharField(max_length=255, blank=True, help_text="Sanskrit title (Unicode)")
    title_ta = models.CharField(max_length=255, blank=True, help_text="Tamil title (Unicode)")
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class Lesson(AuditableModel):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    title_sa = models.CharField(max_length=255, blank=True)
    title_ta = models.CharField(max_length=255, blank=True)
    content_text = models.TextField(blank=True, help_text="Unicode lesson body (Sanskrit/Tamil/English)")
    sort_order = models.PositiveIntegerField(default=0)
    estimated_minutes = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class LessonResource(AuditableModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.CharField(max_length=10, choices=ResourceType.choices)
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    s3_bucket = models.CharField(max_length=100, blank=True)
    s3_key = models.CharField(max_length=500, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    text_body = models.TextField(blank=True, help_text="Inline Unicode text when resource_type=TEXT")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.lesson.title} – {self.title}"
