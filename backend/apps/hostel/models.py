from django.db import models

from apps.core.models import AuditableModel


class HostelStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class RoomStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    OCCUPIED = "OCCUPIED", "Occupied"
    MAINTENANCE = "MAINTENANCE", "Maintenance"


class AssignmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    ENDED = "ENDED", "Ended"


class LeaveStatus(models.TextChoices):
    IN_RESIDENCE = "IN_RESIDENCE", "In Residence"
    ON_LEAVE = "ON_LEAVE", "On Leave"


class Hostel(AuditableModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="hostels")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    warden = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warden_hostels",
    )
    status = models.CharField(max_length=20, choices=HostelStatus.choices, default=HostelStatus.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "code"], name="unique_hostel_code_per_branch"),
        ]

    def __str__(self):
        return f"{self.name} ({self.branch.code})"


class HostelRoom(AuditableModel):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=20)
    floor = models.CharField(max_length=10, blank=True)
    capacity = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=RoomStatus.choices, default=RoomStatus.AVAILABLE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["hostel", "room_number"], name="unique_room_per_hostel"),
        ]

    def __str__(self):
        return f"{self.hostel.code} – {self.room_number}"


class RoomAssignment(AuditableModel):
    room = models.ForeignKey(HostelRoom, on_delete=models.PROTECT, related_name="assignments")
    student = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="room_assignments")
    check_in = models.DateField()
    check_out = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.ACTIVE)
    leave_status = models.CharField(max_length=20, choices=LeaveStatus.choices, default=LeaveStatus.IN_RESIDENCE)
    mess_eligible = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["room", "status"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["leave_status", "status"]),
        ]

    def __str__(self):
        return f"{self.student.email} @ {self.room}"
