import base64

from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chant_evaluator.models import ChantEvaluation
from apps.chant_evaluator.serializers import ChantEvaluateSerializer, ChantEvaluationSerializer
from apps.chant_evaluator.services import ChantEvaluationService, SanskritPhoneticScorer
from apps.curriculum.models import Lesson
from apps.rbac.permissions import require_permission


class ChantEvaluationListView(generics.ListAPIView):
    permission_classes = [require_permission("chant.view")]
    serializer_class = ChantEvaluationSerializer

    def get_queryset(self):
        qs = ChantEvaluation.objects.filter(is_deleted=False).order_by("-created_at")
        if not self.request.user.is_superuser:
            qs = qs.filter(student=self.request.user)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})


class ChantEvaluateView(APIView):
    permission_classes = [require_permission("chant.evaluate")]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        lesson = None
        reference_text = request.data.get("reference_text", "")
        lesson_id = request.data.get("lesson_id")
        duration_seconds = request.data.get("duration_seconds")

        if lesson_id:
            lesson = generics.get_object_or_404(Lesson, id=lesson_id, is_deleted=False)
            if not reference_text and lesson.content_text:
                reference_text = lesson.content_text

        audio_file = request.FILES.get("audio")
        if audio_file:
            audio_bytes = audio_file.read()
        elif request.data.get("audio_base64"):
            audio_bytes = base64.b64decode(request.data["audio_base64"])
        else:
            return Response({"success": False, "error": {"message": "Audio recording required."}}, status=400)

        if not reference_text:
            return Response({"success": False, "error": {"message": "Reference text required."}}, status=400)

        evaluation = ChantEvaluationService.evaluate(
            request.user,
            reference_text,
            audio_bytes,
            lesson=lesson,
            duration_seconds=int(duration_seconds) if duration_seconds else None,
        )
        return Response({"success": True, "data": ChantEvaluationSerializer(evaluation).data}, status=201)


class ChantScorePreviewView(APIView):
    """Score spoken text without persisting — useful for low-latency UI feedback."""

    permission_classes = [require_permission("chant.evaluate")]

    def post(self, request):
        reference = request.data.get("reference_text", "")
        spoken = request.data.get("spoken_text", "")
        if not reference or not spoken:
            return Response({"success": False, "error": {"message": "reference_text and spoken_text required."}}, status=400)
        result = SanskritPhoneticScorer.score(reference, spoken)
        return Response({"success": True, "data": result})
