from django.db.models import Count
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import set_audit_context
from apps.gurukulam_feedback.models import GurukulamFeedback, GurukulamFeedbackHistory
from apps.gurukulam_feedback.serializers import (
    GurukulamFeedbackHistorySerializer,
    GurukulamFeedbackSerializer,
    GurukulamFeedbackStatusSerializer,
    GurukulamFeedbackSubmitSerializer,
)
from apps.gurukulam_feedback.services import GurukulamFeedbackService
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService


def _can_manage(user):
    return PermissionService.user_has_permission(user, "gurukulam_feedback.manage")


class GurukulamFeedbackSubmitView(APIView):
    """General Gurukulam feedback — all users and anonymous visitors. No DevOps routing."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GurukulamFeedbackSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user if request.user.is_authenticated else None
        is_anon = data.get("is_anonymous", False)

        if user and not is_anon and not PermissionService.user_has_permission(user, "gurukulam_feedback.add"):
            return Response({"success": False, "error": {"message": "Permission denied."}}, status=403)

        feedback = GurukulamFeedback.objects.create(
            reporter=None if is_anon else user,
            reporter_email=data.get("reporter_email") or (user.email if user else ""),
            reporter_type="" if is_anon else (user.user_type if user else ""),
            is_anonymous=is_anon,
            branch=getattr(request, "branch", None),
            category=data.get("category", "SUGGESTION"),
            title=data["title"],
            description=data["description"],
        )
        GurukulamFeedbackService.submit(feedback, actor=user)
        return Response({"success": True, "data": GurukulamFeedbackSerializer(feedback).data}, status=201)


class GurukulamFeedbackListView(generics.ListAPIView):
    permission_classes = [require_permission("gurukulam_feedback.view")]
    serializer_class = GurukulamFeedbackSerializer

    def get_queryset(self):
        qs = GurukulamFeedback.objects.filter(is_deleted=False).select_related("reporter", "responded_by").order_by("-created_at")
        if not _can_manage(self.request.user):
            qs = qs.filter(reporter=self.request.user)
        status = self.request.query_params.get("status")
        category = self.request.query_params.get("category")
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})


class GurukulamFeedbackDetailView(APIView):
    permission_classes = [require_permission("gurukulam_feedback.view")]

    def get(self, request, id):
        feedback = generics.get_object_or_404(GurukulamFeedback, id=id, is_deleted=False)
        if not _can_manage(request.user) and feedback.reporter_id != request.user.id:
            return Response({"success": False, "error": {"message": "Not found."}}, status=404)
        history = GurukulamFeedbackHistory.objects.filter(feedback=feedback).order_by("-occurred_at")[:20]
        return Response({
            "success": True,
            "data": {
                "feedback": GurukulamFeedbackSerializer(feedback).data,
                "history": GurukulamFeedbackHistorySerializer(history, many=True).data,
            },
        })


class GurukulamFeedbackStatusUpdateView(APIView):
    permission_classes = [require_permission("gurukulam_feedback.manage")]

    def patch(self, request, id):
        feedback = generics.get_object_or_404(GurukulamFeedback, id=id, is_deleted=False)
        serializer = GurukulamFeedbackStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        feedback = GurukulamFeedbackService.update_status(
            feedback,
            serializer.validated_data["status"],
            request.user,
            serializer.validated_data.get("reason", ""),
            serializer.validated_data.get("admin_response", ""),
        )
        return Response({"success": True, "data": GurukulamFeedbackSerializer(feedback).data})


class GurukulamFeedbackStatsView(APIView):
    permission_classes = [require_permission("gurukulam_feedback.manage")]

    def get(self, request):
        qs = GurukulamFeedback.objects.filter(is_deleted=False)
        by_status = dict(qs.values_list("status").annotate(c=Count("id")).values_list("status", "c"))
        by_category = dict(qs.values_list("category").annotate(c=Count("id")).values_list("category", "c"))
        return Response({
            "success": True,
            "data": {
                "total": qs.count(),
                "by_status": by_status,
                "by_category": by_category,
                "pending_review": qs.filter(status="SUBMITTED").count(),
            },
        })
