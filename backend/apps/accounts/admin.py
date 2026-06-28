from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import (
    AcharyaProfile,
    BranchAdminProfile,
    DonorProfile,
    HostelWardenProfile,
    ParentProfile,
    PasswordResetToken,
    RefreshToken,
    StudentProfile,
    User,
    UserProfile,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "user_type", "account_status", "is_staff", "created_at"]
    list_filter = ["user_type", "account_status", "is_staff"]
    search_fields = ["email", "profile__first_name", "profile__last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Classification", {"fields": ("user_type", "account_status", "email_verified_at")}),
        ("Security", {"fields": ("failed_login_attempts", "locked_until", "must_change_password", "last_password_change_at")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Lifecycle", {"fields": ("is_deleted", "deleted_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "user_type", "password1", "password2", "account_status"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


admin.site.register(UserProfile)
admin.site.register(StudentProfile)
admin.site.register(ParentProfile)
admin.site.register(AcharyaProfile)
admin.site.register(BranchAdminProfile)
admin.site.register(DonorProfile)
admin.site.register(HostelWardenProfile)
admin.site.register(RefreshToken)
admin.site.register(PasswordResetToken)
