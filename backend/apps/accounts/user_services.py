from django.db import transaction

from apps.accounts.models import (
    AcharyaProfile,
    BranchAdminProfile,
    DonorProfile,
    HostelWardenProfile,
    ParentProfile,
    StudentProfile,
    User,
    UserProfile,
)
from apps.accounts.services import PROFILE_MODEL_MAP


TYPE_PROFILE_MODELS = {
    "student_profile": StudentProfile,
    "parent_profile": ParentProfile,
    "acharya_profile": AcharyaProfile,
    "branch_admin_profile": BranchAdminProfile,
    "donor_profile": DonorProfile,
    "hostel_warden_profile": HostelWardenProfile,
}


class UserService:
    @classmethod
    @transaction.atomic
    def create_user(cls, data, actor=None):
        profile_data = data.pop("profile", {}) or {}
        type_profile_data = data.pop("type_profile", {}) or {}
        password = data.pop("password")
        account_status = data.get("account_status")
        user = User.objects.create_user(password=password, **data)

        if account_status is None:
            from apps.accounts.models import AccountStatus
            from django.utils import timezone

            user.account_status = AccountStatus.ACTIVE
            user.email_verified_at = timezone.now()
            user.save(update_fields=["account_status", "email_verified_at", "updated_at"])

        if profile_data:
            UserProfile.objects.filter(user=user).update(**profile_data)

        attr = PROFILE_MODEL_MAP.get(user.user_type)
        if attr:
            model = TYPE_PROFILE_MODELS[attr]
            model.objects.create(user=user, **type_profile_data)

        return user

    @classmethod
    @transaction.atomic
    def update_user(cls, user, data):
        profile_data = data.pop("profile", None)
        for field, value in data.items():
            setattr(user, field, value)
        user.save()

        if profile_data:
            UserProfile.objects.filter(user=user).update(**profile_data)
        return user

    @classmethod
    @transaction.atomic
    def soft_delete_user(cls, user, actor):
        from apps.accounts.services import AuthenticationService

        user.soft_delete(actor=actor)
        AuthenticationService.revoke_all_sessions(user)
        user.role_assignments.filter(is_active=True).update(is_active=False)
        user.branch_memberships.filter(is_active=True).update(is_active=False)
        return user
