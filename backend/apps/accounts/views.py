from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.serializers import (
    AccountStatusSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from apps.accounts.services import AccountStatusService, AuthenticationService
from apps.accounts.user_services import UserService
from apps.core.context import set_audit_context
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, tokens = AuthenticationService.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            request=request,
            branch_id=serializer.validated_data.get("branch_id"),
        )
        return Response(
            {
                "success": True,
                "data": {
                    "tokens": tokens,
                    "user": UserSerializer(user).data,
                },
            }
        )


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = AuthenticationService.refresh(serializer.validated_data["refresh"], request)
        return Response({"success": True, "data": tokens})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthenticationService.logout(serializer.validated_data["refresh"], request)
        return Response({"success": True, "message": "Logged out successfully."})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = AuthenticationService.request_password_reset(serializer.validated_data["email"], request)
        data = {"message": "If the email exists, a reset link has been sent."}
        if token and request.query_params.get("debug") == "true":
            data["debug_token"] = token
        return Response({"success": True, "data": data})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthenticationService.confirm_password_reset(
            serializer.validated_data["token"],
            serializer.validated_data["password"],
            request,
        )
        return Response({"success": True, "message": "Password reset successful."})


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return User.objects.select_related("profile").get(pk=self.request.user.pk)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        branch_id = getattr(request, "branch_id", None)
        permissions = sorted(PermissionService.get_user_permissions(user, branch_id=branch_id))
        return Response(
            {
                "success": True,
                "data": {
                    "user": UserSerializer(user).data,
                    "permissions": permissions,
                    "is_super_admin": PermissionService.user_has_super_admin(user),
                    "branch_id": str(branch_id) if branch_id else None,
                },
            }
        )


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthenticationService.change_password(
            request.user,
            serializer.validated_data["current_password"],
            serializer.validated_data["new_password"],
            request,
        )
        return Response({"success": True, "message": "Password changed successfully."})


class UserForceLogoutView(APIView):
    permission_classes = [require_permission("users.change")]

    def post(self, request, id):
        user = generics.get_object_or_404(User, id=id)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        AuthenticationService.revoke_all_sessions(user)
        return Response({"success": True, "message": "All sessions revoked."})


class UserListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("users.view")]
    serializer_class = UserSerializer
    queryset = User.objects.select_related("profile").order_by("-created_at")
    search_fields = ["email", "profile__first_name", "profile__last_name"]
    ordering_fields = ["created_at", "email"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("users.add")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        user = UserService.create_user(serializer.validated_data, actor=request.user)
        return Response(
            {"success": True, "data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.select_related("profile")
    serializer_class = UserSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method == "GET":
            return [require_permission("users.view")()]
        if self.request.method in ("PUT", "PATCH"):
            return [require_permission("users.change")()]
        return [require_permission("users.delete")()]

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        user = UserService.update_user(user, serializer.validated_data)
        return Response({"success": True, "data": UserSerializer(user).data})

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        UserService.soft_delete_user(user, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserStatusView(APIView):
    permission_classes = [require_permission("users.change")]

    def post(self, request, id):
        user = generics.get_object_or_404(User, id=id)
        serializer = AccountStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        user = AccountStatusService.transition(
            user,
            serializer.validated_data["account_status"],
            actor=request.user,
            request=request,
        )
        return Response({"success": True, "data": UserSerializer(user).data})


class UserVerifyEmailView(APIView):
    permission_classes = [require_permission("users.change")]

    def post(self, request, id):
        user = generics.get_object_or_404(User, id=id)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        user = AccountStatusService.verify_email(user)
        return Response({"success": True, "data": UserSerializer(user).data})
