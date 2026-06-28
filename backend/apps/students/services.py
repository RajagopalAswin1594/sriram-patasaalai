from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import AccountStatus, User, UserType
from apps.accounts.user_services import UserService
from apps.academics.models import Batch
from apps.branches.models import Branch, UserBranchMembership
from apps.branches.services import BranchMembershipService
from apps.core.exceptions import ConflictError, DomainError
from apps.rbac.models import Role
from apps.rbac.services import RoleAssignmentService
from apps.students.models import (
    BatchEnrollment,
    BatchEnrollmentStatus,
    EnrollmentStatus,
    ParentChildLink,
    StudentBranchEnrollment,
)


class ParentAccessService:
    @staticmethod
    def child_student_ids(parent_user: User):
        return list(
            ParentChildLink.objects.filter(
                parent=parent_user,
                is_verified=True,
                is_deleted=False,
            ).values_list("student_id", flat=True)
        )

    @classmethod
    def filter_students_for_user(cls, user: User, queryset):
        from apps.rbac.services import PermissionService

        if PermissionService.user_has_super_admin(user):
            return queryset
        if user.user_type == UserType.PARENT:
            child_ids = cls.child_student_ids(user)
            return queryset.filter(student_id__in=child_ids)
        return queryset


class StudentEnrollmentService:
    @classmethod
    @transaction.atomic
    def create_active_student(cls, data: dict, actor):
        branch_id = data.pop("branch_id")
        batch_id = data.pop("batch_id", None)
        profile = data.pop("profile", {})
        type_profile = data.pop("type_profile", {})

        user_data = {
            "email": data["email"],
            "password": data["password"],
            "user_type": UserType.STUDENT,
            "account_status": AccountStatus.ACTIVE,
            "profile": profile,
            "type_profile": type_profile,
        }
        user = UserService.create_user(user_data, actor=actor)

        branch = Branch.objects.get(id=branch_id)
        BranchMembershipService.add_membership(user, branch, is_primary=True)
        role = Role.objects.filter(code="student", is_deleted=False).first()
        if role:
            RoleAssignmentService.assign_role(user, role, branch=branch, assigned_by=actor)

        enrollment = StudentBranchEnrollment.objects.create(
            student=user,
            branch_id=branch_id,
            status=EnrollmentStatus.ACTIVE,
        )

        if batch_id:
            cls.assign_batch(enrollment, batch_id, effective_from=data.get("effective_from"))

        return user, enrollment

    @classmethod
    @transaction.atomic
    def assign_batch(cls, student_enrollment: StudentBranchEnrollment, batch_id, effective_from=None):
        batch = Batch.objects.filter(id=batch_id, is_deleted=False, is_active=True).first()
        if not batch:
            raise DomainError("Batch not found.")
        if batch.branch_id != student_enrollment.branch_id:
            raise DomainError("Batch must belong to the student's branch.")

        effective_from = effective_from or timezone.now().date()
        cls._close_active_batch_enrollments(student_enrollment, effective_from, reason="Batch reassignment")

        return BatchEnrollment.objects.create(
            student_enrollment=student_enrollment,
            batch=batch,
            status=BatchEnrollmentStatus.ACTIVE,
            effective_from=effective_from,
        )

    @classmethod
    @transaction.atomic
    def bulk_assign_batch(cls, batch_id, student_ids: list, effective_from=None, actor=None):
        batch = Batch.objects.filter(id=batch_id, is_deleted=False, is_active=True).first()
        if not batch:
            raise DomainError("Batch not found.")

        effective_from = effective_from or timezone.now().date()
        results = []
        for student_id in student_ids:
            enrollment = StudentBranchEnrollment.objects.filter(
                student_id=student_id,
                branch_id=batch.branch_id,
                status=EnrollmentStatus.ACTIVE,
                is_deleted=False,
            ).first()
            if not enrollment:
                enrollment = StudentBranchEnrollment.objects.create(
                    student_id=student_id,
                    branch_id=batch.branch_id,
                    status=EnrollmentStatus.ACTIVE,
                )
            batch_enrollment = cls.assign_batch(enrollment, batch.id, effective_from=effective_from)
            results.append(batch_enrollment)
        return results

    @classmethod
    @transaction.atomic
    def transfer_batch(
        cls,
        student_id,
        from_batch_id,
        to_batch_id,
        effective_date: date | None = None,
        reason: str = "",
    ):
        effective_date = effective_date or timezone.now().date()
        from_enrollment = BatchEnrollment.objects.select_related("student_enrollment").filter(
            student_enrollment__student_id=student_id,
            batch_id=from_batch_id,
            status=BatchEnrollmentStatus.ACTIVE,
            is_deleted=False,
        ).first()
        if not from_enrollment:
            raise DomainError("Active enrollment in source batch not found.")

        from_enrollment.status = BatchEnrollmentStatus.TRANSFERRED
        from_enrollment.effective_to = effective_date
        from_enrollment.transfer_reason = reason
        from_enrollment.save(update_fields=["status", "effective_to", "transfer_reason", "updated_at"])

        return cls.assign_batch(from_enrollment.student_enrollment, to_batch_id, effective_from=effective_date)

    @classmethod
    def _close_active_batch_enrollments(cls, student_enrollment, close_date, reason=""):
        active = BatchEnrollment.objects.filter(
            student_enrollment=student_enrollment,
            status=BatchEnrollmentStatus.ACTIVE,
            is_deleted=False,
        )
        for record in active:
            record.status = BatchEnrollmentStatus.TRANSFERRED
            record.effective_to = close_date
            record.transfer_reason = reason
            record.save(update_fields=["status", "effective_to", "transfer_reason", "updated_at"])

    @classmethod
    @transaction.atomic
    def link_parent_child(cls, parent_id, student_id, relationship_type, is_primary=True, is_verified=True):
        parent = User.objects.filter(id=parent_id, user_type=UserType.PARENT, is_deleted=False).first()
        student = User.objects.filter(id=student_id, user_type=UserType.STUDENT, is_deleted=False).first()
        if not parent or not student:
            raise DomainError("Valid parent and student users are required.")

        link, _ = ParentChildLink.objects.update_or_create(
            parent=parent,
            student=student,
            defaults={
                "relationship_type": relationship_type,
                "is_primary": is_primary,
                "is_verified": is_verified,
                "is_deleted": False,
                "deleted_at": None,
                "deleted_by": None,
            },
        )
        return link
