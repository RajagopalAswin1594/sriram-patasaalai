from django.db import transaction

from apps.branches.models import Branch, UserBranchMembership
from apps.core.exceptions import DomainError


class BranchMembershipService:
    @classmethod
    @transaction.atomic
    def add_membership(cls, user, branch, is_primary=False):
        if UserBranchMembership.objects.filter(user=user, branch=branch, is_deleted=False).exists():
            membership = UserBranchMembership.objects.get(user=user, branch=branch, is_deleted=False)
            membership.is_active = True
            membership.save(update_fields=["is_active", "updated_at"])
        else:
            membership = UserBranchMembership.objects.create(user=user, branch=branch, is_primary=is_primary)

        if is_primary:
            cls.set_primary(user, branch)
        return membership

    @classmethod
    @transaction.atomic
    def set_primary(cls, user, branch):
        UserBranchMembership.objects.filter(user=user, is_active=True, is_deleted=False).update(is_primary=False)
        updated = UserBranchMembership.objects.filter(user=user, branch=branch, is_deleted=False).update(is_primary=True)
        if not updated:
            raise DomainError("User is not a member of this branch.")

    @classmethod
    @transaction.atomic
    def remove_membership(cls, user, branch):
        membership = UserBranchMembership.objects.filter(user=user, branch=branch, is_deleted=False).first()
        if not membership:
            raise DomainError("Membership not found.")
        membership.is_active = False
        membership.is_primary = False
        membership.save(update_fields=["is_active", "is_primary", "updated_at"])
