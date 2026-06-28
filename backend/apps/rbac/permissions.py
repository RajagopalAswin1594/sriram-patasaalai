from django.db import models
from django.utils import timezone
from rest_framework.permissions import BasePermission

from apps.rbac.services import PermissionService


class HasPermission(BasePermission):
    permission_codename = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        codename = getattr(view, "permission_codename", None) or self.permission_codename
        if not codename:
            return False
        branch_id = getattr(request, "branch_id", None)
        return PermissionService.user_has_permission(request.user, codename, branch_id=branch_id)


def require_permission(codename):
    class _Permission(HasPermission):
        permission_codename = codename

    return _Permission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and PermissionService.user_has_super_admin(request.user)
