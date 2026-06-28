from django.utils.dateparse import parse_datetime
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User, UserType
from apps.accounts.serializers import UserSerializer
from apps.academics.models import Batch
from apps.branches.models import Branch
from apps.core.branch_scope import branch_scoped_queryset
from apps.core.context import set_audit_context
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService
from apps.scheduling.models import AcharyaBranchAssignment, AcharyaShakhaSpecialization, TeachingSession
from apps.scheduling.serializers import (
    AcharyaBranchSerializer,
    AcharyaMappingSerializer,
    AcharyaRegisterSerializer,
    AcharyaShakhaSerializer,
    TeachingSessionCreateSerializer,
    TeachingSessionSerializer,
)
from apps.scheduling.services import SchedulingService


class TeachingSessionListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("scheduling.view")]
    serializer_class = TeachingSessionSerializer

    def get_queryset(self):
        qs = TeachingSession.objects.select_related("acharya", "batch", "branch", "course").filter(is_deleted=False)
        qs = branch_scoped_queryset(self.request.user, qs)

        if self.request.user.user_type == UserType.ACHARYA and not PermissionService.user_has_super_admin(
            self.request.user
        ):
            qs = qs.filter(acharya=self.request.user)

        from_dt = self.request.query_params.get("from")
        to_dt = self.request.query_params.get("to")
        if from_dt:
            qs = qs.filter(ends_at__gte=parse_datetime(from_dt))
        if to_dt:
            qs = qs.filter(starts_at__lte=parse_datetime(to_dt))
        return qs.order_by("starts_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("scheduling.add")()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        serializer = TeachingSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))

        acharya = generics.get_object_or_404(User, id=data["acharya_id"], user_type=UserType.ACHARYA)
        batch = generics.get_object_or_404(Batch, id=data["batch_id"])
        branch = generics.get_object_or_404(Branch, id=data["branch_id"])

        session = SchedulingService.create_session(
            {
                "acharya": acharya,
                "batch": batch,
                "branch": branch,
                "course_id": data.get("course_id"),
                "title": data["title"],
                "starts_at": data["starts_at"],
                "ends_at": data["ends_at"],
                "timezone": data.get("timezone", "Asia/Kolkata"),
                "location": data.get("location", ""),
                "notes": data.get("notes", ""),
            },
            actor=request.user,
        )
        return Response({"success": True, "data": TeachingSessionSerializer(session).data}, status=201)


class AcharyaRegisterView(APIView):
    permission_classes = [require_permission("scheduling.add")]

    def post(self, request):
        serializer = AcharyaRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        user = SchedulingService.register_acharya(serializer.validated_data, actor=request.user)
        return Response({"success": True, "data": UserSerializer(user).data}, status=201)


class AcharyaPortalView(APIView):
    permission_classes = [require_permission("scheduling.view")]

    def get(self, request):
        if request.user.user_type != UserType.ACHARYA and not PermissionService.user_has_super_admin(request.user):
            return Response({"success": False, "error": {"message": "Acharya access only."}}, status=403)

        acharya = request.user
        branches = AcharyaBranchAssignment.objects.filter(acharya=acharya, is_deleted=False).select_related("branch")
        shakhas = AcharyaShakhaSpecialization.objects.filter(acharya=acharya, is_deleted=False).select_related("shakha")
        from_dt = parse_datetime(request.query_params.get("from", "")) if request.query_params.get("from") else None
        to_dt = parse_datetime(request.query_params.get("to", "")) if request.query_params.get("to") else None
        sessions = SchedulingService.get_acharya_calendar(acharya, from_dt, to_dt)

        return Response(
            {
                "success": True,
                "data": {
                    "branches": AcharyaBranchSerializer(branches, many=True).data,
                    "shakhas": AcharyaShakhaSerializer(shakhas, many=True).data,
                    "sessions": TeachingSessionSerializer(sessions, many=True).data,
                },
            }
        )


class AcharyaMappingView(APIView):
    permission_classes = [require_permission("scheduling.change")]

    def post(self, request):
        serializer = AcharyaMappingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        acharya = generics.get_object_or_404(User, id=serializer.validated_data["acharya_id"], user_type=UserType.ACHARYA)

        AcharyaBranchAssignment.objects.filter(acharya=acharya).update(is_deleted=True)
        AcharyaShakhaSpecialization.objects.filter(acharya=acharya).update(is_deleted=True)

        for index, branch_id in enumerate(serializer.validated_data["branch_ids"]):
            AcharyaBranchAssignment.objects.update_or_create(
                acharya=acharya,
                branch_id=branch_id,
                defaults={"is_primary": index == 0, "is_deleted": False, "deleted_at": None},
            )
        for index, shakha_id in enumerate(serializer.validated_data["shakha_ids"]):
            AcharyaShakhaSpecialization.objects.update_or_create(
                acharya=acharya,
                shakha_id=shakha_id,
                defaults={"is_primary": index == 0, "is_deleted": False, "deleted_at": None},
            )

        return Response({"success": True, "message": "Acharya mappings updated."})
