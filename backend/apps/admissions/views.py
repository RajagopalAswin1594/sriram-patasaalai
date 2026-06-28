from django.db.models import Count, Q
from django.http import FileResponse, Http404, StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.admissions.document_review import DocumentReviewService
from apps.admissions.models import AdmissionApplication, ApplicationDocument, ApplicationStatus
from apps.admissions.payment import PaymentService
from apps.admissions.review import ReviewWorkflowService
from apps.admissions.serializers import (
    AdminApplicationListSerializer,
    AdmissionApplicationSerializer,
    ApplicationAssignSerializer,
    ApplicationReviewSerializer,
    ApplicationStatusHistorySerializer,
    DocumentConfirmSerializer,
    DocumentPresignSerializer,
    DocumentReviewSerializer,
    PaymentConfirmSerializer,
    PublicApplicationCreateSerializer,
    PublicApplicationUpdateSerializer,
    PublicBranchSerializer,
)
from apps.admissions.services import ApplicationService
from apps.admissions.storage import StorageService
from apps.branches.models import Branch, BranchStatus
from apps.core.context import set_audit_context
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService


def _branch_scoped_queryset(user, queryset):
    if PermissionService.user_has_super_admin(user):
        return queryset
    branch_ids = user.branch_memberships.filter(is_active=True, is_deleted=False).values_list("branch_id", flat=True)
    return queryset.filter(branch_id__in=branch_ids)


class PublicBranchListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        branches = Branch.objects.filter(status=BranchStatus.ACTIVE, is_deleted=False).order_by("name")
        data = PublicBranchSerializer(branches, many=True).data
        return Response({"success": True, "data": data})


class PublicApplicationCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PublicApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        branch_id = data.pop("branch_id")
        application = ApplicationService.create_draft({**data, "branch_id": branch_id})
        return Response(
            {"success": True, "data": AdmissionApplicationSerializer(application).data},
            status=status.HTTP_201_CREATED,
        )


class PublicApplicationDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, id):
        token = request.query_params.get("access_token", "")
        application = ApplicationService.get_public_application(id, token)
        return Response({"success": True, "data": AdmissionApplicationSerializer(application).data})

    def patch(self, request, id):
        token = request.data.get("access_token") or request.query_params.get("access_token", "")
        application = ApplicationService.get_public_application(id, token)
        serializer = PublicApplicationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        application = ApplicationService.update_draft(application, serializer.validated_data)
        return Response({"success": True, "data": AdmissionApplicationSerializer(application).data})


class PublicApplicationSubmitView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, id):
        token = request.data.get("access_token", "")
        application = ApplicationService.get_public_application(id, token)
        application = ApplicationService.submit(application)
        return Response({"success": True, "data": AdmissionApplicationSerializer(application).data})


class DocumentPresignView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, id):
        serializer = DocumentPresignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = ApplicationService.get_public_application(id, serializer.validated_data["access_token"])
        try:
            document, presigned = ApplicationService.presign_document(
                application,
                serializer.validated_data["document_type"],
                serializer.validated_data["file_name"],
                serializer.validated_data["content_type"],
                serializer.validated_data["file_size"],
            )
        except ValueError as exc:
            return Response(
                {"success": False, "error": {"code": "validation_error", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "success": True,
                "data": {
                    "document_id": str(document.id),
                    "upload": presigned,
                },
            }
        )


class DocumentConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, id):
        serializer = DocumentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = ApplicationService.get_public_application(id, serializer.validated_data["access_token"])
        document = ApplicationService.confirm_document_upload(application, serializer.validated_data["document_id"])
        from apps.admissions.serializers import ApplicationDocumentSerializer

        return Response({"success": True, "data": ApplicationDocumentSerializer(document).data})


class LocalDocumentUploadView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if StorageService.is_s3_enabled():
            return Response(
                {"success": False, "error": {"code": "not_allowed", "message": "Use S3 upload."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        uploaded = request.FILES.get("file")
        s3_key = request.data.get("key")
        if not uploaded or not s3_key:
            return Response(
                {"success": False, "error": {"code": "validation_error", "message": "file and key required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        StorageService.save_local_file(s3_key, uploaded)
        return Response({"success": True, "message": "Uploaded."})


class PaymentInitiateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, id):
        token = request.data.get("access_token", "")
        application = ApplicationService.get_public_application(id, token)
        payment_data = PaymentService.initiate_payment(application)
        return Response({"success": True, "data": payment_data})


class PaymentConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, id):
        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = ApplicationService.get_public_application(id, serializer.validated_data["access_token"])

        if PaymentService.is_razorpay_enabled():
            PaymentService.verify_razorpay_payment(
                application,
                serializer.validated_data["order_id"],
                serializer.validated_data["payment_id"],
                serializer.validated_data["signature"],
            )
        else:
            PaymentService.confirm_demo_payment(application)

        application.refresh_from_db()
        return Response({"success": True, "data": AdmissionApplicationSerializer(application).data})


class AdminApplicationListView(generics.ListAPIView):
    permission_classes = [require_permission("admissions.view")]
    serializer_class = AdminApplicationListSerializer
    filterset_fields = ["status", "branch_id"]
    search_fields = ["application_number", "student_first_name", "parent_name", "parent_phone"]
    ordering_fields = ["created_at", "submitted_at"]

    def get_queryset(self):
        qs = AdmissionApplication.objects.select_related(
            "branch", "payment", "reviewed_by", "assigned_to"
        ).prefetch_related("documents", "status_history", "notifications")
        qs = _branch_scoped_queryset(self.request.user, qs)
        status_filter = self.request.query_params.get("status")
        if status_filter == "PENDING":
            qs = qs.filter(status__in=[ApplicationStatus.PENDING, "UNDER_REVIEW"])
        return qs.order_by("-submitted_at", "-created_at")


class AdminApplicationDetailView(generics.RetrieveAPIView):
    permission_classes = [require_permission("admissions.view")]
    serializer_class = AdmissionApplicationSerializer
    lookup_field = "id"

    def get_queryset(self):
        qs = AdmissionApplication.objects.select_related(
            "branch", "payment", "reviewed_by", "assigned_to"
        ).prefetch_related("documents", "status_history", "notifications")
        return _branch_scoped_queryset(self.request.user, qs)


class AdminApplicationStatsView(APIView):
    permission_classes = [require_permission("admissions.view")]

    def get(self, request):
        qs = _branch_scoped_queryset(request.user, AdmissionApplication.objects.filter(is_deleted=False))
        pending = qs.filter(status__in=[ApplicationStatus.PENDING, "UNDER_REVIEW"]).count()
        approved = qs.filter(status=ApplicationStatus.APPROVED).count()
        rejected = qs.filter(status=ApplicationStatus.REJECTED).count()
        stale = ReviewWorkflowService.get_stale_pending_applications().filter(
            id__in=qs.values_list("id", flat=True)
        ).count()
        return Response(
            {
                "success": True,
                "data": {
                    "pending": pending,
                    "approved": approved,
                    "rejected": rejected,
                    "stale_pending": stale,
                    "total": qs.count(),
                },
            }
        )


class AdminApplicationReviewView(APIView):
    permission_classes = [require_permission("admissions.approve")]

    def post(self, request, id):
        application = generics.get_object_or_404(
            _branch_scoped_queryset(request.user, AdmissionApplication.objects.all()),
            id=id,
        )
        serializer = ApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        application = ApplicationService.review(
            application,
            serializer.validated_data["status"],
            request.user,
            serializer.validated_data.get("rejection_reason", ""),
            serializer.validated_data.get("review_notes", ""),
        )
        application.refresh_from_db()
        return Response({"success": True, "data": AdmissionApplicationSerializer(application).data})


class AdminApplicationAssignView(APIView):
    permission_classes = [require_permission("admissions.change")]

    def post(self, request, id):
        application = generics.get_object_or_404(
            _branch_scoped_queryset(request.user, AdmissionApplication.objects.all()),
            id=id,
        )
        serializer = ApplicationAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reviewer = generics.get_object_or_404(User, id=serializer.validated_data["assigned_to_id"])
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        application = ReviewWorkflowService.assign_reviewer(application, reviewer, request.user)
        return Response({"success": True, "data": AdmissionApplicationSerializer(application).data})


class AdminApplicationHistoryView(APIView):
    permission_classes = [require_permission("admissions.view")]

    def get(self, request, id):
        application = generics.get_object_or_404(
            _branch_scoped_queryset(request.user, AdmissionApplication.objects.all()),
            id=id,
        )
        history = application.status_history.all()
        return Response({"success": True, "data": ApplicationStatusHistorySerializer(history, many=True).data})


class AdminDocumentViewView(APIView):
    """Stream application document inline for portal preview (no download attachment)."""

    permission_classes = [require_permission("admissions.view")]

    def get(self, request, id, document_id):
        application = generics.get_object_or_404(
            _branch_scoped_queryset(request.user, AdmissionApplication.objects.all()),
            id=id,
        )
        document = ApplicationDocument.objects.filter(application=application, id=document_id, is_deleted=False).first()
        if not document:
            raise Http404("Document not found.")

        try:
            stream, content_type, file_name = StorageService.open_document_stream(document)
        except FileNotFoundError as exc:
            raise Http404(str(exc)) from exc

        disposition = f'inline; filename="{file_name}"'
        if hasattr(stream, "read"):
            response = FileResponse(stream, content_type=content_type, as_attachment=False)
        else:
            response = StreamingHttpResponse(stream, content_type=content_type)

        response["Content-Disposition"] = disposition
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class AdminDocumentReviewView(APIView):
    permission_classes = [require_permission("admissions.approve")]

    def post(self, request, id, document_id):
        application = generics.get_object_or_404(
            _branch_scoped_queryset(request.user, AdmissionApplication.objects.all()),
            id=id,
        )
        document = ApplicationDocument.objects.filter(application=application, id=document_id, is_deleted=False).first()
        if not document:
            raise Http404("Document not found.")

        serializer = DocumentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        document = DocumentReviewService.review(
            document,
            serializer.validated_data["action"],
            request.user,
            serializer.validated_data.get("reason", ""),
            serializer.validated_data.get("notify_channels"),
        )
        application.refresh_from_db()
        return Response({"success": True, "data": AdmissionApplicationSerializer(application).data})
