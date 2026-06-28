from rest_framework import serializers

from apps.hostel.models import Hostel, HostelRoom, RoomAssignment


class HostelSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    warden_email = serializers.CharField(source="warden.email", read_only=True, allow_null=True)

    class Meta:
        model = Hostel
        fields = (
            "id",
            "branch_id",
            "branch_code",
            "code",
            "name",
            "address",
            "capacity",
            "warden_id",
            "warden_email",
            "status",
        )


class HostelRoomSerializer(serializers.ModelSerializer):
    hostel_code = serializers.CharField(source="hostel.code", read_only=True)
    active_occupants = serializers.SerializerMethodField()

    class Meta:
        model = HostelRoom
        fields = (
            "id",
            "hostel_id",
            "hostel_code",
            "room_number",
            "floor",
            "capacity",
            "status",
            "active_occupants",
        )

    def get_active_occupants(self, obj):
        return obj.assignments.filter(status="ACTIVE", is_deleted=False).count()


class RoomAssignmentSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source="room.room_number", read_only=True)
    hostel_code = serializers.CharField(source="room.hostel.code", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = RoomAssignment
        fields = (
            "id",
            "room_id",
            "room_number",
            "hostel_code",
            "student_id",
            "student_email",
            "student_name",
            "check_in",
            "check_out",
            "status",
            "leave_status",
            "mess_eligible",
        )

    def get_student_name(self, obj):
        return getattr(obj.student.profile, "display_name", obj.student.email)


class RoomAssignmentCreateSerializer(serializers.Serializer):
    room_id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    check_in = serializers.DateField()


class LeaveStatusUpdateSerializer(serializers.Serializer):
    leave_status = serializers.ChoiceField(choices=["IN_RESIDENCE", "ON_LEAVE"])
