from rest_framework import serializers

from apps.chant_evaluator.models import ChantEvaluation


class ChantEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChantEvaluation
        fields = (
            "id",
            "lesson_id",
            "reference_text",
            "transcribed_text",
            "phonetic_score",
            "syllable_scores",
            "feedback",
            "evaluation_mode",
            "duration_seconds",
            "created_at",
        )


class ChantEvaluateSerializer(serializers.Serializer):
    reference_text = serializers.CharField()
    lesson_id = serializers.UUIDField(required=False, allow_null=True)
    duration_seconds = serializers.IntegerField(required=False, allow_null=True)
    audio_base64 = serializers.CharField(required=False, allow_blank=True)
