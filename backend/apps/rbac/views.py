from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import set_audit_context
from apps.rbac.models import Permission, Role, RolePermission, UserRoleAssignment
from apps.rbac.permissions import require_permission
from apps.rbac.serializers import (
    PermissionSerializer,
    RoleCreateUpdateSerializer,
    RolePermissionSerializer,
    RoleSerializer,
    UserRoleAssignmentSerializer,
)
from apps.rbac.services import RoleAssignmentService


class PermissionListView(generics.ListAPIView):
    permission_classes = [require_permission("permissions.view")]
    serializer_class = PermissionSerializer
    queryset = Permission.objects.order_by("module", "action")
    filterset_fields = ["module", "action"]
    search_fields = ["codename", "name", "module"]


class RoleListCreateView(generics.ListCreateAPIView):
    serializer_class = RoleSerializer
    queryset = Role.objects.prefetch_related("permissions").order_by("-priority", "name")
    search_fields = ["code", "name"]
    filterset_fields = ["scope_type", "is_active", "is_system"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("roles.add")()]
        return [require_permission("roles.view")()]

    def create(self, request, *args, **kwargs):
        serializer = RoleCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        role = Role.objects.create(**serializer.validated_data)
        return Response(
            {"success": True, "data": RoleSerializer(role).data},
            status=status.HTTP_201_CREATED,
        )


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.prefetch_related("permissions")
    serializer_class = RoleSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method == "GET":
            return [require_permission("roles.view")()]
        if self.request.method in ("PUT", "PATCH"):
            return [require_permission("roles.change")()]
        return [require_permission("roles.delete")()]

    def update(self, request, *args, **kwargs):
        role = self.get_object()
        if role.is_system and "code" in request.data:
            return Response(
                {"success": False, "error": {"code": "domain_error", "message": "System role code cannot be changed."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RoleCreateUpdateSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        for field, value in serializer.validated_data.items():
            setattr(role, field, value)
        role.save()
        return Response({"success": True, "data": RoleSerializer(role).data})

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if role.is_system:
            return Response(
                {"success": False, "error": {"code": "domain_error", "message": "System roles cannot be deleted."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        role.soft_delete(actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolePermissionView(APIView):
    permission_classes = [require_permission("roles.change")]

    def post(self, request, id):
        role = generics.get_object_or_404(Role, id=id)
        serializer = RolePermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission = generics.get_object_or_404(Permission, id=serializer.validated_data["permission_id"])
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        RolePermission.objects.get_or_create(role=role, permission=permission, defaults={"granted_by": request.user})
        return Response({"success": True, "data": RoleSerializer(role).data})

    def delete(self, request, id):
        role = generics.get_object_or_404(Role, id=id)
        permission_id = request.data.get("permission_id")
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        RolePermission.objects.filter(role=role, permission_id=permission_id).update(is_deleted=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRoleAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = UserRoleAssignmentSerializer
    filterset_fields = ["user_id", "role_id", "branch_id", "is_active"]

    def get_queryset(self):
        return UserRoleAssignment.objects.select_related("user", "role", "branch").order_by("-assigned_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("roles.change")()]
        return [require_permission("roles.view")()]

    def create(self, request, *args, **kwargs):
        serializer = UserRoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        assignment = RoleAssignmentService.assign_role(
            user=serializer.validated_data["user"],
            role=serializer.validated_data["role"],
            branch=serializer.validated_data.get("branch"),
            assigned_by=request.user,
            expires_at=serializer.validated_data.get("expires_at"),
        )
        return Response(
            {"success": True, "data": UserRoleAssignmentSerializer(assignment).data},
            status=status.HTTP_201_CREATED,
        )


class UserRoleAssignmentDetailView(generics.DestroyAPIView):
    permission_classes = [require_permission("roles.change")]
    queryset = UserRoleAssignment.objects.all()
    lookup_field = "id"

    def destroy(self, request, *args, **kwargs):
        assignment = self.get_object()
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        RoleAssignmentService.revoke_role(assignment.user, assignment.role, assignment.branch)
        return Response(status=status.HTTP_204_NO_CONTENT)
