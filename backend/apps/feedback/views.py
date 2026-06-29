from django.conf import settings
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import set_audit_context
from apps.feedback.models import Feedback, FeedbackComment, FeedbackHistory, FeedbackStatus
from apps.feedback.serializers import (
    FeedbackCommentCreateSerializer,
    FeedbackCommentSerializer,
    FeedbackHistorySerializer,
    FeedbackSerializer,
    FeedbackStatusUpdateSerializer,
    FeedbackSubmitSerializer,
)
from config.feedback_integrations import integration_status

from apps.feedback.github_sync import IntegrationMessage

from apps.feedback.response_utils import feedback_api_response
from apps.feedback.services import FeedbackWorkflowService, GitHubIntegrationService
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService


def _can_manage(user):
    return PermissionService.user_has_permission(user, "feedback.manage")


class FeedbackSubmitView(APIView):
    """Application development feedback — Super Admin only. Routes to AI + GitHub/DevOps."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not PermissionService.user_has_super_admin(request.user):
            return Response(
                {"success": False, "error": {"message": "Only Super Admins can submit application development feedback."}},
                status=403,
            )
        serializer = FeedbackSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        is_anon = False

        feedback = Feedback.objects.create(
            reporter=user,
            reporter_email=user.email,
            reporter_type=user.user_type,
            is_anonymous=is_anon,
            branch=getattr(request, "branch", None),
            category=data.get("category", "BUG"),
            source_module=data.get("source_module", "PLATFORM"),
            environment=data.get("environment", getattr(settings, "FEEDBACK_DEFAULT_ENV", "PRODUCTION")),
            platform=data.get("platform", "WEB"),
            app_version=data.get("app_version", ""),
            browser_device=data.get("browser_device", request.META.get("HTTP_USER_AGENT", "")[:255]),
            screen_name=data.get("screen_name", ""),
            title=data["title"],
            description=data["description"],
            steps_to_reproduce=data.get("steps_to_reproduce", ""),
            expected_result=data.get("expected_result", ""),
            actual_result=data.get("actual_result", ""),
        )
        feedback, messages, github_sync = FeedbackWorkflowService.submit_and_process(feedback, actor=user)
        feedback.refresh_from_db()
        return Response(feedback_api_response(feedback, messages, github_sync), status=201)


class FeedbackListView(generics.ListAPIView):
    permission_classes = [require_permission("feedback.view")]
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        qs = Feedback.objects.filter(is_deleted=False).select_related(
            "analysis", "github_issue", "duplicate_of", "reporter"
        ).order_by("-created_at")
        if not _can_manage(self.request.user):
            qs = qs.filter(reporter=self.request.user)
        status = self.request.query_params.get("status")
        module = self.request.query_params.get("module")
        env = self.request.query_params.get("environment")
        if status:
            qs = qs.filter(status=status)
        if module:
            qs = qs.filter(source_module=module)
        if env:
            qs = qs.filter(environment=env)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})


class FeedbackDetailView(APIView):
    permission_classes = [require_permission("feedback.view")]

    def get(self, request, id):
        feedback = generics.get_object_or_404(
            Feedback.objects.select_related("analysis", "github_issue", "duplicate_of"),
            id=id,
            is_deleted=False,
        )
        if not _can_manage(request.user) and feedback.reporter_id != request.user.id:
            return Response({"success": False, "error": {"message": "Not found."}}, status=404)
        history = FeedbackHistory.objects.filter(feedback=feedback).order_by("-occurred_at")[:20]
        comments = FeedbackComment.objects.filter(feedback=feedback, is_deleted=False)
        if not _can_manage(request.user):
            comments = comments.filter(is_internal=False)
        return Response({
            "success": True,
            "data": {
                "feedback": FeedbackSerializer(feedback).data,
                "history": FeedbackHistorySerializer(history, many=True).data,
                "comments": FeedbackCommentSerializer(comments, many=True).data,
            },
        })


class FeedbackApproveGitHubView(APIView):
    permission_classes = [require_permission("feedback.manage")]

    def post(self, request, id):
        feedback = generics.get_object_or_404(Feedback, id=id, is_deleted=False)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        mapping, github_sync = FeedbackWorkflowService.create_github_issue(feedback, actor=request.user)
        feedback.refresh_from_db()
        messages = list(github_sync.messages)
        if mapping:
            messages.insert(0, IntegrationMessage(level="info", code="github_approved", text=f"GitHub issue #{mapping.issue_number} created."))
        return Response(feedback_api_response(feedback, messages, github_sync, github=mapping and {
            "issue_number": mapping.issue_number,
            "issue_url": mapping.issue_url,
            "sync_mode": mapping.sync_mode,
        }))


class FeedbackStatusUpdateView(APIView):
    permission_classes = [require_permission("feedback.manage")]

    def patch(self, request, id):
        feedback = generics.get_object_or_404(Feedback, id=id, is_deleted=False)
        serializer = FeedbackStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        feedback = FeedbackWorkflowService.update_status(
            feedback, serializer.validated_data["status"], request.user, serializer.validated_data.get("reason", "")
        )
        return Response({"success": True, "data": FeedbackSerializer(feedback).data})


class FeedbackCommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        feedback = generics.get_object_or_404(Feedback, id=id, is_deleted=False)
        if not _can_manage(request.user) and feedback.reporter_id != request.user.id:
            return Response({"success": False, "error": {"message": "Forbidden."}}, status=403)
        serializer = FeedbackCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_internal = serializer.validated_data.get("is_internal", True) and _can_manage(request.user)
        comment = FeedbackComment.objects.create(
            feedback=feedback,
            author=request.user,
            body=serializer.validated_data["body"],
            is_internal=is_internal,
        )
        return Response({"success": True, "data": FeedbackCommentSerializer(comment).data}, status=201)


class FeedbackStatsView(APIView):
    permission_classes = [require_permission("feedback.manage")]

    def get(self, request):
        from django.db.models import Count

        qs = Feedback.objects.filter(is_deleted=False)
        by_status = {s: c for s, c in qs.values_list("status").annotate(c=Count("id")).values_list("status", "c")}
        by_module = {m: c for m, c in qs.values_list("source_module").annotate(c=Count("id")).values_list("source_module", "c")}
        pending_github = qs.filter(status=FeedbackStatus.PENDING_APPROVAL).count()
        return Response({
            "success": True,
            "data": {
                "by_status": by_status,
                "by_module": by_module,
                "pending_github_approval": pending_github,
                "total": qs.count(),
            },
        })


class FeedbackIntegrationsView(APIView):
    """Sanitized integration status for ops (no secrets)."""
    permission_classes = [require_permission("feedback.manage")]

    def get(self, request):
        integrations = settings.FEEDBACK_INTEGRATIONS
        general = integrations["general"]
        status = integration_status(settings)
        return Response({
            "success": True,
            "data": {
                "default_env": general["default_env"],
                "issue_tracker": general["issue_tracker"],
                "auto_create_issue": general["auto_create_issue"],
                "providers": {
                    "github": {
                        "enabled": integrations["github"]["enabled"],
                        "configured": status["github"],
                        "repo": integrations["github"]["repo"] or None,
                        "api_url": integrations["github"]["api_url"],
                        "labels": [
                            label.strip()
                            for label in str(integrations["github"]["labels"] or "").split(",")
                            if label.strip()
                        ],
                        "milestone": integrations["github"]["milestone"] or None,
                        "project_configured": bool(integrations["github"]["project_node_id"]),
                        "default_branch": integrations["github"]["default_branch"] or None,
                        "branch_prefix": integrations["github"]["branch_prefix"] or None,
                        "branch_name_template": integrations["github"]["branch_name_template"],
                        "gurukulam_id": integrations["github"]["gurukulam_id"] or None,
                        "auto_create_branch": integrations["github"]["auto_create_branch"],
                    },
                    "gitlab": {
                        "enabled": integrations["gitlab"]["enabled"],
                        "configured": status["gitlab"],
                        "project_id": integrations["gitlab"]["project_id"] or None,
                        "api_url": integrations["gitlab"]["api_url"],
                    },
                    "jira": {
                        "enabled": integrations["jira"]["enabled"],
                        "configured": status["jira"],
                        "base_url": integrations["jira"]["base_url"] or None,
                        "project_key": integrations["jira"]["project_key"] or None,
                    },
                    "azure_boards": {
                        "enabled": integrations["azure_boards"]["enabled"],
                        "configured": status["azure_boards"],
                        "organization": integrations["azure_boards"]["organization"] or None,
                        "project": integrations["azure_boards"]["project"] or None,
                        "work_item_type": integrations["azure_boards"]["work_item_type"],
                    },
                    "slack": {
                        "enabled": integrations["slack"]["enabled"],
                        "configured": status["slack"],
                        "channel": integrations["slack"]["channel"],
                        "notify_on_submit": integrations["slack"]["notify_on_submit"],
                        "notify_on_issue_created": integrations["slack"]["notify_on_issue_created"],
                    },
                },
            },
        })


class FeedbackGitHubTestView(APIView):
    """Test GitHub token/repo connectivity without creating an issue."""
    permission_classes = [require_permission("feedback.manage")]

    def post(self, request):
        sync = GitHubIntegrationService.test_connection()
        status_code = 200 if sync.success or sync.mode == "DISABLED" else 502
        return Response({"success": sync.success, "github_sync": sync.as_dict()}, status=status_code)
