from django.contrib import admin

from apps.rbac.models import Permission, Role, RolePermission, UserRoleAssignment


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "scope_type", "is_system", "is_active", "priority"]
    search_fields = ["code", "name"]
    list_filter = ["scope_type", "is_system", "is_active"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["codename", "module", "action", "name"]
    search_fields = ["codename", "name", "module"]
    list_filter = ["module", "action"]


admin.site.register(RolePermission)
admin.site.register(UserRoleAssignment)
