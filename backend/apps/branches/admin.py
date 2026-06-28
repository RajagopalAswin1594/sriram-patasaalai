from django.contrib import admin

from apps.branches.models import Branch, UserBranchMembership


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "status", "city", "is_headquarters"]
    search_fields = ["code", "name", "city"]
    list_filter = ["status", "is_headquarters"]


admin.site.register(UserBranchMembership)
