from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, UserType
from apps.core.branch_scope import branch_scoped_queryset
from apps.core.exceptions import DomainError
from apps.hostel.models import AssignmentStatus, Hostel, HostelRoom, LeaveStatus, RoomAssignment, RoomStatus


class HostelService:
    @staticmethod
    def hostel_queryset(user):
        qs = Hostel.objects.filter(is_deleted=False).select_related("branch", "warden")
        return branch_scoped_queryset(user, qs, branch_field="branch_id")

    @staticmethod
    def room_queryset(user):
        qs = HostelRoom.objects.filter(is_deleted=False).select_related("hostel", "hostel__branch")
        hostel_ids = HostelService.hostel_queryset(user).values_list("id", flat=True)
        return qs.filter(hostel_id__in=hostel_ids)

    @staticmethod
    def assignment_queryset(user):
        qs = RoomAssignment.objects.filter(is_deleted=False).select_related(
            "room", "room__hostel", "student", "student__profile"
        )
        hostel_ids = HostelService.hostel_queryset(user).values_list("id", flat=True)
        return qs.filter(room__hostel_id__in=hostel_ids)

    @classmethod
    @transaction.atomic
    def assign_student(cls, room: HostelRoom, student: User, check_in):
        if student.user_type != UserType.STUDENT:
            raise DomainError("Only students can be assigned to hostel rooms.")
        active = RoomAssignment.objects.filter(
            student=student, status=AssignmentStatus.ACTIVE, is_deleted=False
        ).exists()
        if active:
            raise DomainError("Student already has an active room assignment.")
        active_in_room = RoomAssignment.objects.filter(
            room=room, status=AssignmentStatus.ACTIVE, is_deleted=False
        ).count()
        if active_in_room >= room.capacity:
            raise DomainError("Room is at full capacity.")
        assignment = RoomAssignment.objects.create(
            room=room,
            student=student,
            check_in=check_in,
            status=AssignmentStatus.ACTIVE,
            leave_status=LeaveStatus.IN_RESIDENCE,
            mess_eligible=True,
        )
        cls._sync_room_status(room)
        return assignment

    @classmethod
    @transaction.atomic
    def update_leave_status(cls, assignment: RoomAssignment, leave_status: str):
        assignment.leave_status = leave_status
        assignment.mess_eligible = leave_status == LeaveStatus.IN_RESIDENCE
        assignment.save(update_fields=["leave_status", "mess_eligible", "updated_at"])

        from apps.notifications.services import NotificationDispatcher

        student_name = getattr(assignment.student.profile, "display_name", assignment.student.email)
        NotificationDispatcher.send(
            template_code="HOSTEL_LEAVE_ALERT",
            recipient_phone=getattr(assignment.student.profile, "phone", "") or "",
            context={
                "student_name": student_name,
                "leave_status": leave_status.replace("_", " ").title(),
                "hostel_name": assignment.room.hostel.name,
            },
            idempotency_key=f"hostel-leave-{assignment.id}-{leave_status}",
            channels=["SMS", "WHATSAPP"],
        )
        return assignment

    @classmethod
    def _sync_room_status(cls, room: HostelRoom):
        count = RoomAssignment.objects.filter(room=room, status=AssignmentStatus.ACTIVE, is_deleted=False).count()
        if count >= room.capacity:
            room.status = RoomStatus.OCCUPIED
        elif room.status != RoomStatus.MAINTENANCE:
            room.status = RoomStatus.AVAILABLE if count == 0 else RoomStatus.OCCUPIED
        room.save(update_fields=["status", "updated_at"])

    @classmethod
    def occupancy_map(cls, user, hostel_id=None):
        hostels = cls.hostel_queryset(user)
        if hostel_id:
            hostels = hostels.filter(id=hostel_id)
        result = []
        for hostel in hostels:
            rooms = []
            for room in hostel.rooms.filter(is_deleted=False).order_by("floor", "room_number"):
                assignments = RoomAssignment.objects.filter(
                    room=room, status=AssignmentStatus.ACTIVE, is_deleted=False
                ).select_related("student", "student__profile")
                rooms.append(
                    {
                        "id": str(room.id),
                        "room_number": room.room_number,
                        "floor": room.floor,
                        "capacity": room.capacity,
                        "status": room.status,
                        "occupants": [
                            {
                                "assignment_id": str(a.id),
                                "student_id": str(a.student_id),
                                "student_name": getattr(a.student.profile, "display_name", a.student.email),
                                "leave_status": a.leave_status,
                                "mess_eligible": a.mess_eligible,
                                "check_in": a.check_in.isoformat(),
                            }
                            for a in assignments
                        ],
                    }
                )
            result.append(
                {
                    "id": str(hostel.id),
                    "code": hostel.code,
                    "name": hostel.name,
                    "branch_id": str(hostel.branch_id),
                    "branch_code": hostel.branch.code,
                    "capacity": hostel.capacity,
                    "rooms": rooms,
                }
            )
        return result

    @classmethod
    def warden_portal(cls, user):
        hostels = cls.hostel_queryset(user).filter(warden=user)
        if not hostels.exists() and not user.is_superuser:
            hostels = cls.hostel_queryset(user)
        on_leave = cls.assignment_queryset(user).filter(
            status=AssignmentStatus.ACTIVE,
            leave_status=LeaveStatus.ON_LEAVE,
            room__hostel__in=hostels,
        ).count()
        in_residence = cls.assignment_queryset(user).filter(
            status=AssignmentStatus.ACTIVE,
            leave_status=LeaveStatus.IN_RESIDENCE,
            room__hostel__in=hostels,
        ).count()
        return {
            "hostels": list(hostels.values("id", "code", "name", "branch_id")),
            "stats": {
                "on_leave": on_leave,
                "in_residence": in_residence,
                "mess_eligible": in_residence,
            },
            "occupancy": cls.occupancy_map(user),
        }
