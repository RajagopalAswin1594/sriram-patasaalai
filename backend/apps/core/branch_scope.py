from apps.rbac.services import PermissionService


def branch_scoped_queryset(user, queryset, branch_field="branch_id"):
    if PermissionService.user_has_super_admin(user):
        return queryset
    branch_ids = user.branch_memberships.filter(is_active=True, is_deleted=False).values_list(
        "branch_id", flat=True
    )
    return queryset.filter(**{f"{branch_field}__in": branch_ids})
