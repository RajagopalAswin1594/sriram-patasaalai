from django.db import models, transaction
from django.utils import timezone

from apps.core.exceptions import ConflictError, DomainError, PermissionDeniedError
from apps.rbac.models import Role, RoleScopeType, UserRoleAssignment


class PermissionService:
    SUPER_ADMIN_ROLE_CODE = "super_admin"

    @classmethod
    def user_has_super_admin(cls, user):
        return cls.get_user_role_codes(user).filter(role__code=cls.SUPER_ADMIN_ROLE_CODE).exists()

    @classmethod
    def get_user_role_codes(cls, user, branch_id=None):
        qs = UserRoleAssignment.objects.filter(user=user, is_active=True, is_deleted=False).select_related("role")
        qs = qs.filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))
        if branch_id:
            qs = qs.filter(models.Q(branch_id=branch_id) | models.Q(branch__isnull=True, role__scope_type=RoleScopeType.GLOBAL))
        return qs

    @classmethod
    def get_user_permissions(cls, user, branch_id=None):
        if cls.user_has_super_admin(user):
            return {"*"}
        assignments = cls.get_user_role_codes(user, branch_id=branch_id)
        permissions = set()
        for assignment in assignments:
            if branch_id and assignment.role.scope_type == RoleScopeType.BRANCH:
                if assignment.branch_id and str(assignment.branch_id) != str(branch_id):
                    continue
            permissions.update(
                assignment.role.permissions.filter(is_deleted=False).values_list("codename", flat=True)
            )
        return permissions

    @classmethod
    def user_has_permission(cls, user, codename, branch_id=None):
        if cls.user_has_super_admin(user):
            return True
        return codename in cls.get_user_permissions(user, branch_id=branch_id)

    @classmethod
    def assert_permission(cls, user, codename, branch_id=None):
        if not cls.user_has_permission(user, codename, branch_id=branch_id):
            raise PermissionDeniedError(f"Missing permission: {codename}")


class RoleAssignmentService:
    @classmethod
    @transaction.atomic
    def assign_role(cls, user, role, branch=None, assigned_by=None, expires_at=None):
        if role.scope_type == RoleScopeType.BRANCH and branch is None:
            raise DomainError("Branch is required for branch-scoped roles.")
        if role.scope_type == RoleScopeType.GLOBAL and branch is not None:
            raise DomainError("Global roles cannot be branch-scoped.")

        if role.scope_type == RoleScopeType.BRANCH:
            from apps.branches.models import UserBranchMembership

            if not UserBranchMembership.objects.filter(
                user=user, branch=branch, is_active=True, is_deleted=False
            ).exists():
                raise DomainError("User must belong to the branch before role assignment.")

        if assigned_by and not PermissionService.user_has_super_admin(assigned_by):
            assigner_permissions = PermissionService.get_user_permissions(
                assigned_by, branch_id=str(branch.id) if branch else None
            )
            role_permissions = set(role.permissions.values_list("codename", flat=True))
            if not role_permissions.issubset(assigner_permissions):
                raise PermissionDeniedError("Cannot assign a role with permissions exceeding your own.")

        assignment, created = UserRoleAssignment.objects.get_or_create(
            user=user,
            role=role,
            branch=branch,
            defaults={
                "assigned_by": assigned_by,
                "expires_at": expires_at,
                "is_active": True,
            },
        )
        if not created:
            assignment.is_active = True
            assignment.expires_at = expires_at
            assignment.assigned_by = assigned_by
            assignment.save()
        return assignment

    @classmethod
    @transaction.atomic
    def revoke_role(cls, user, role, branch=None):
        if role.is_system and role.code == PermissionService.SUPER_ADMIN_ROLE_CODE:
            remaining = UserRoleAssignment.objects.filter(
                role=role,
                is_active=True,
                is_deleted=False,
            ).exclude(user=user).count()
            if remaining == 0:
                raise ConflictError("Cannot remove the last super admin.")

        UserRoleAssignment.objects.filter(user=user, role=role, branch=branch).update(is_active=False)
