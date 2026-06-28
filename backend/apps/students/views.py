from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserType
from apps.accounts.serializers import UserSerializer
from apps.core.branch_scope import branch_scoped_queryset
from apps.core.context import set_audit_context
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService
from apps.students.models import ParentChildLink, StudentBranchEnrollment
from apps.students.serializers import (
    BulkBatchAssignSerializer,
    BatchTransferSerializer,
    CreateStudentSerializer,
    ParentChildLinkCreateSerializer,
    ParentChildLinkSerializer,
    StudentBranchEnrollmentSerializer,
)
from apps.students.services import ParentAccessService, StudentEnrollmentService


class StudentEnrollmentListView(generics.ListAPIView):
    permission_classes = [require_permission("students.view")]
    serializer_class = StudentBranchEnrollmentSerializer

    def get_queryset(self):
        qs = StudentBranchEnrollment.objects.select_related("student", "student__profile", "branch").filter(
            is_deleted=False
        )
        qs = branch_scoped_queryset(self.request.user, qs)
        qs = ParentAccessService.filter_students_for_user(self.request.user, qs)
        return qs.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class CreateStudentView(APIView):
    permission_classes = [require_permission("students.add")]

    def post(self, request):
        serializer = CreateStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        user, enrollment = StudentEnrollmentService.create_active_student(serializer.validated_data, request.user)
        return Response(
            {
                "success": True,
                "data": {
                    "user": UserSerializer(user).data,
                    "enrollment": StudentBranchEnrollmentSerializer(enrollment).data,
                },
            },
            status=201,
        )


class BulkBatchAssignView(APIView):
    permission_classes = [require_permission("students.change")]

    def post(self, request):
        serializer = BulkBatchAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        results = StudentEnrollmentService.bulk_assign_batch(
            serializer.validated_data["batch_id"],
            serializer.validated_data["student_ids"],
            effective_from=serializer.validated_data.get("effective_from"),
            actor=request.user,
        )
        return Response({"success": True, "data": {"assigned_count": len(results)}})


class BatchTransferView(APIView):
    permission_classes = [require_permission("students.change")]

    def post(self, request):
        serializer = BatchTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        enrollment = StudentEnrollmentService.transfer_batch(
            serializer.validated_data["student_id"],
            serializer.validated_data["from_batch_id"],
            serializer.validated_data["to_batch_id"],
            effective_date=serializer.validated_data.get("effective_date"),
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"success": True, "data": {"batch_enrollment_id": str(enrollment.id)}})


class ParentChildLinkListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("students.view")]
    serializer_class = ParentChildLinkSerializer

    def get_queryset(self):
        qs = ParentChildLink.objects.select_related("parent", "student", "student__profile").filter(is_deleted=False)
        if self.request.user.user_type == UserType.PARENT and not PermissionService.user_has_super_admin(
            self.request.user
        ):
            qs = qs.filter(parent=self.request.user)
        return qs.order_by("-created_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("students.change")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        create_serializer = ParentChildLinkCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        link = StudentEnrollmentService.link_parent_child(**create_serializer.validated_data)
        return Response({"success": True, "data": ParentChildLinkSerializer(link).data}, status=201)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class MyChildrenView(APIView):
    permission_classes = [require_permission("students.view")]

    def get(self, request):
        if request.user.user_type != UserType.PARENT and not PermissionService.user_has_super_admin(request.user):
            return Response({"success": True, "data": []})
        child_ids = ParentAccessService.child_student_ids(request.user)
        qs = StudentBranchEnrollment.objects.filter(student_id__in=child_ids, is_deleted=False).select_related(
            "student", "student__profile", "branch"
        )
        return Response({"success": True, "data": StudentBranchEnrollmentSerializer(qs, many=True).data})
