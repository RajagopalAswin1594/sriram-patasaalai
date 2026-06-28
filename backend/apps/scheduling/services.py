from django.db import transaction
from django.utils import timezone

from apps.accounts.models import AccountStatus, UserType
from apps.accounts.user_services import UserService
from apps.branches.models import Branch
from apps.branches.services import BranchMembershipService
from apps.core.exceptions import ConflictError, DomainError
from apps.rbac.models import Role
from apps.rbac.services import RoleAssignmentService
from apps.scheduling.models import AcharyaBranchAssignment, AcharyaShakhaSpecialization, SessionStatus, TeachingSession


class SchedulingConflictError(ConflictError):
    pass


class SchedulingService:
    @classmethod
    def acharya_has_conflict(cls, acharya_id, starts_at, ends_at, exclude_session_id=None) -> bool:
        qs = TeachingSession.objects.filter(
            acharya_id=acharya_id,
            status=SessionStatus.SCHEDULED,
            is_deleted=False,
            starts_at__lt=ends_at,
            ends_at__gt=starts_at,
        )
        if exclude_session_id:
            qs = qs.exclude(id=exclude_session_id)
        return qs.exists()

    @classmethod
    @transaction.atomic
    def create_session(cls, data: dict, actor=None):
        acharya = data["acharya"]
        starts_at = data["starts_at"]
        ends_at = data["ends_at"]
        if ends_at <= starts_at:
            raise DomainError("Session end must be after start.")

        if cls.acharya_has_conflict(acharya.id, starts_at, ends_at):
            raise SchedulingConflictError("Acharya is already scheduled during this time slot.")

        batch = data["batch"]
        if batch.branch_id != data["branch"].id:
            raise DomainError("Batch must belong to the selected branch.")

        course = data.pop("course", None)
        if data.get("course_id"):
            from apps.academics.models import VedicCourse
            course = VedicCourse.objects.filter(id=data.pop("course_id")).first()

        return TeachingSession.objects.create(**data, course=course)

    @classmethod
    @transaction.atomic
    def update_session(cls, session: TeachingSession, data: dict):
        starts_at = data.get("starts_at", session.starts_at)
        ends_at = data.get("ends_at", session.ends_at)
        acharya_id = data.get("acharya_id", session.acharya_id)

        if ends_at <= starts_at:
            raise DomainError("Session end must be after start.")

        if cls.acharya_has_conflict(acharya_id, starts_at, ends_at, exclude_session_id=session.id):
            raise SchedulingConflictError("Acharya is already scheduled during this time slot.")

        for field, value in data.items():
            setattr(session, field, value)
        session.save()
        return session

    @classmethod
    @transaction.atomic
    def register_acharya(cls, data: dict, actor=None):
        branch_ids = data.pop("branch_ids", [])
        shakha_ids = data.pop("shakha_ids", [])
        profile = data.pop("profile", {})
        type_profile = data.pop("type_profile", {})

        user_data = {
            "email": data["email"],
            "password": data["password"],
            "user_type": UserType.ACHARYA,
            "account_status": AccountStatus.ACTIVE,
            "profile": profile,
            "type_profile": type_profile,
        }
        user = UserService.create_user(user_data, actor=actor)

        role = Role.objects.filter(code="acharya", is_deleted=False).first()
        for index, branch_id in enumerate(branch_ids):
            branch = Branch.objects.get(id=branch_id)
            BranchMembershipService.add_membership(user, branch, is_primary=index == 0)
            AcharyaBranchAssignment.objects.get_or_create(
                acharya=user,
                branch_id=branch_id,
                defaults={"is_primary": index == 0},
            )
            if role:
                RoleAssignmentService.assign_role(user, role, branch=branch, assigned_by=actor)

        for index, shakha_id in enumerate(shakha_ids):
            AcharyaShakhaSpecialization.objects.get_or_create(
                acharya=user,
                shakha_id=shakha_id,
                defaults={"is_primary": index == 0},
            )

        return user

    @classmethod
    def get_acharya_calendar(cls, acharya, from_dt=None, to_dt=None):
        qs = TeachingSession.objects.filter(acharya=acharya, is_deleted=False).select_related(
            "batch", "branch", "course"
        )
        if from_dt:
            qs = qs.filter(ends_at__gte=from_dt)
        if to_dt:
            qs = qs.filter(starts_at__lte=to_dt)
        return qs.order_by("starts_at")
