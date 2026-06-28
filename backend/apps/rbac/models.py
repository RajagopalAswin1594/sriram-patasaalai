from django.db import models

from apps.core.models import AuditableModel


class RoleScopeType(models.TextChoices):
    GLOBAL = "GLOBAL", "Global"
    BRANCH = "BRANCH", "Branch"


class PermissionAction(models.TextChoices):
    VIEW = "VIEW", "View"
    ADD = "ADD", "Add"
    CHANGE = "CHANGE", "Change"
    DELETE = "DELETE", "Delete"
    EXPORT = "EXPORT", "Export"
    IMPORT = "IMPORT", "Import"
    APPROVE = "APPROVE", "Approve"


class Role(AuditableModel):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    scope_type = models.CharField(max_length=10, choices=RoleScopeType.choices)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    permissions = models.ManyToManyField("Permission", through="RolePermission", related_name="roles")

    class Meta:
        ordering = ["-priority", "name"]

    def __str__(self):
        return self.name


class Permission(AuditableModel):
    codename = models.CharField(max_length=100, unique=True)
    module = models.CharField(max_length=50, db_index=True)
    action = models.CharField(max_length=20, choices=PermissionAction.choices)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=True)

    class Meta:
        ordering = ["module", "action"]

    def __str__(self):
        return self.codename


class RolePermission(AuditableModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="granted_role_permissions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="unique_role_permission"),
        ]


class UserRoleAssignment(AuditableModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_assignments")
    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_roles",
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role", "branch"],
                name="unique_user_role_branch",
            ),
        ]

    def __str__(self):
        branch_label = self.branch.code if self.branch else "GLOBAL"
        return f"{self.user.email} -> {self.role.code} @ {branch_label}"
