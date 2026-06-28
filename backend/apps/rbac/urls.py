from django.urls import path

from apps.rbac.views import (
    PermissionListView,
    RoleDetailView,
    RoleListCreateView,
    RolePermissionView,
    UserRoleAssignmentDetailView,
    UserRoleAssignmentListCreateView,
)

urlpatterns = [
    path("permissions/", PermissionListView.as_view(), name="permission-list"),
    path("roles/", RoleListCreateView.as_view(), name="role-list-create"),
    path("roles/<uuid:id>/", RoleDetailView.as_view(), name="role-detail"),
    path("roles/<uuid:id>/permissions/", RolePermissionView.as_view(), name="role-permissions"),
    path("role-assignments/", UserRoleAssignmentListCreateView.as_view(), name="role-assignment-list-create"),
    path("role-assignments/<uuid:id>/", UserRoleAssignmentDetailView.as_view(), name="role-assignment-detail"),
]
