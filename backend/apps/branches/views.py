from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.branches.models import Branch, UserBranchMembership
from apps.branches.serializers import BranchSerializer, UserBranchMembershipSerializer
from apps.branches.services import BranchMembershipService
from apps.core.context import set_audit_context
from apps.rbac.permissions import require_permission


class BranchListCreateView(generics.ListCreateAPIView):
    serializer_class = BranchSerializer
    queryset = Branch.objects.order_by("code")
    search_fields = ["code", "name", "city"]
    filterset_fields = ["status", "is_headquarters"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("branches.add")()]
        return [require_permission("branches.view")()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        branch = serializer.save()
        return Response({"success": True, "data": BranchSerializer(branch).data}, status=status.HTTP_201_CREATED)


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method == "GET":
            return [require_permission("branches.view")()]
        if self.request.method in ("PUT", "PATCH"):
            return [require_permission("branches.change")()]
        return [require_permission("branches.delete")()]

    def update(self, request, *args, **kwargs):
        branch = self.get_object()
        serializer = self.get_serializer(branch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        branch = serializer.save()
        return Response({"success": True, "data": BranchSerializer(branch).data})

    def destroy(self, request, *args, **kwargs):
        branch = self.get_object()
        if UserBranchMembership.objects.filter(branch=branch, is_active=True, is_deleted=False).exists():
            return Response(
                {"success": False, "error": {"code": "conflict", "message": "Branch has active memberships."}},
                status=status.HTTP_409_CONFLICT,
            )
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        branch.soft_delete(actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserBranchMembershipListCreateView(generics.ListCreateAPIView):
    serializer_class = UserBranchMembershipSerializer
    filterset_fields = ["user_id", "branch_id", "is_active", "is_primary"]

    def get_queryset(self):
        return UserBranchMembership.objects.select_related("user", "branch").order_by("-joined_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("branches.change")()]
        return [require_permission("branches.view")()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        membership = BranchMembershipService.add_membership(
            user=serializer.validated_data["user"],
            branch=serializer.validated_data["branch"],
            is_primary=serializer.validated_data.get("is_primary", False),
        )
        return Response(
            {"success": True, "data": UserBranchMembershipSerializer(membership).data},
            status=status.HTTP_201_CREATED,
        )


class UserBranchMembershipDetailView(generics.DestroyAPIView):
    permission_classes = [require_permission("branches.change")]
    queryset = UserBranchMembership.objects.all()
    lookup_field = "id"

    def destroy(self, request, *args, **kwargs):
        membership = self.get_object()
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        BranchMembershipService.remove_membership(membership.user, membership.branch)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetPrimaryBranchView(APIView):
    permission_classes = [require_permission("branches.change")]

    def post(self, request, user_id, branch_id):
        user = generics.get_object_or_404(User, id=user_id)
        branch = generics.get_object_or_404(Branch, id=branch_id)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        BranchMembershipService.set_primary(user, branch)
        return Response({"success": True, "message": "Primary branch updated."})
