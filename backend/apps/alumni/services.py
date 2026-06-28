from django.db import transaction

from apps.accounts.models import AccountStatus, UserType
from apps.accounts.user_services import UserService
from apps.alumni.models import AlumniProfile
from apps.branches.models import Branch
from apps.branches.services import BranchMembershipService
from apps.rbac.models import Role
from apps.rbac.services import RoleAssignmentService


class AlumniRegistrationService:
    @classmethod
    @transaction.atomic
    def register(cls, data: dict):
        branch = None
        if data.get("branch_id"):
            branch = Branch.objects.filter(id=data["branch_id"], is_deleted=False).first()

        user = UserService.create_user(
            {
                "email": data["email"],
                "password": data["password"],
                "user_type": UserType.ALUMNI,
                "account_status": AccountStatus.ACTIVE,
                "profile": {
                    "first_name": data["first_name"],
                    "last_name": data.get("last_name", ""),
                    "phone": data.get("phone", ""),
                },
            },
            actor=None,
        )

        if branch:
            BranchMembershipService.add_membership(user, branch, is_primary=True)

        alumni_role = Role.objects.filter(code="alumni", is_deleted=False).first()
        if alumni_role:
            RoleAssignmentService.assign_role(user, alumni_role, branch=branch, assigned_by=None)

        profile = AlumniProfile.objects.create(
            user=user,
            graduation_year=data["graduation_year"],
            batch_name=data.get("batch_name", ""),
            branch=branch,
            current_city=data.get("current_city", ""),
            current_occupation=data.get("current_occupation", ""),
            bio=data.get("bio", ""),
            is_directory_visible=data.get("is_directory_visible", True),
        )
        return user, profile
