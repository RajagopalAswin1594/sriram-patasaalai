import secrets

from django.db import transaction

from apps.accounts.models import AccountStatus, RelationshipType, User, UserType
from apps.accounts.user_services import UserService
from apps.admissions.models import AdmissionApplication
from apps.branches.services import BranchMembershipService
from apps.rbac.models import Role
from apps.rbac.services import RoleAssignmentService
from apps.students.services import StudentEnrollmentService


class AdmissionProvisioningService:
    """Create student (and optional parent) accounts when an application is approved."""

    @classmethod
    def _student_email(cls, application: AdmissionApplication) -> str:
        slug = application.application_number.lower().replace(" ", "")
        return f"{slug}@students.gurukulam.local"

    @classmethod
    def _temp_password(cls) -> str:
        return f"Welcome@{secrets.token_hex(4)}"

    @classmethod
    @transaction.atomic
    def provision_from_application(cls, application: AdmissionApplication, actor):
        if application.provisioned_student_id:
            return User.objects.get(id=application.provisioned_student_id)

        password = cls._temp_password()
        student_email = cls._student_email(application)

        user, enrollment = StudentEnrollmentService.create_active_student(
            {
                "email": student_email,
                "password": password,
                "branch_id": application.branch_id,
                "profile": {
                    "first_name": application.student_first_name,
                    "last_name": application.student_last_name,
                    "phone": application.parent_phone,
                    "preferred_language": application.preferred_language,
                },
                "type_profile": {
                    "admission_number": application.application_number,
                    "date_of_birth": application.date_of_birth,
                },
            },
            actor=actor,
        )

        if application.parent_email:
            parent = User.objects.filter(email=application.parent_email.lower(), is_deleted=False).first()
            if not parent:
                rel = application.relationship.upper()
                if rel not in RelationshipType.values:
                    rel = RelationshipType.GUARDIAN
                parent = UserService.create_user(
                    {
                        "email": application.parent_email,
                        "password": cls._temp_password(),
                        "user_type": UserType.PARENT,
                        "account_status": AccountStatus.ACTIVE,
                        "profile": {
                            "first_name": application.parent_name.split()[0] if application.parent_name else "Parent",
                            "last_name": " ".join(application.parent_name.split()[1:]) if application.parent_name else "",
                            "phone": application.parent_phone,
                        },
                        "type_profile": {"relationship_type": rel},
                    },
                    actor=actor,
                )
                BranchMembershipService.add_membership(parent, application.branch, is_primary=True)
                parent_role = Role.objects.filter(code="parent", is_deleted=False).first()
                if parent_role:
                    RoleAssignmentService.assign_role(parent, parent_role, branch=application.branch, assigned_by=actor)

            StudentEnrollmentService.link_parent_child(
                parent.id,
                user.id,
                application.relationship.upper() if application.relationship.upper() in RelationshipType.values else "GUARDIAN",
            )

        application.provisioned_student = user
        application.save(update_fields=["provisioned_student", "updated_at"])
        return user
