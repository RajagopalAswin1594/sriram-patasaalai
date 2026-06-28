from django.urls import path

from apps.accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshTokenView,
    UserDetailView,
    UserForceLogoutView,
    UserListCreateView,
    UserStatusView,
    UserVerifyEmailView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("auth/password-change/", PasswordChangeView.as_view(), name="auth-password-change"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("users/<uuid:id>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<uuid:id>/force-logout/", UserForceLogoutView.as_view(), name="user-force-logout"),
    path("users/<uuid:id>/status/", UserStatusView.as_view(), name="user-status"),
    path("users/<uuid:id>/verify-email/", UserVerifyEmailView.as_view(), name="user-verify-email"),
]
