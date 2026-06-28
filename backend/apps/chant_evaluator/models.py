from django.db import models

from apps.core.models import AuditableModel


class EvaluationMode(models.TextChoices):
    DEMO = "DEMO", "Demo"
    AI = "AI", "AI"


class ChantEvaluation(AuditableModel):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="chant_evaluations")
    lesson = models.ForeignKey("curriculum.Lesson", on_delete=models.SET_NULL, null=True, blank=True)
    reference_text = models.TextField(help_text="Expected chant in IAST or transliteration")
    transcribed_text = models.TextField(blank=True)
    phonetic_score = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    syllable_scores = models.JSONField(default=list)
    feedback = models.TextField(blank=True)
    evaluation_mode = models.CharField(max_length=10, choices=EvaluationMode.choices, default=EvaluationMode.DEMO)
    audio_s3_bucket = models.CharField(max_length=100, blank=True)
    audio_s3_key = models.CharField(max_length=500, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["student", "created_at"])]
