from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.core.context import set_audit_context
from apps.core.exceptions import DomainError
from apps.hostel.models import Hostel, HostelRoom, RoomAssignment
from apps.hostel.serializers import (
    HostelRoomSerializer,
    HostelSerializer,
    LeaveStatusUpdateSerializer,
    RoomAssignmentCreateSerializer,
    RoomAssignmentSerializer,
)
from apps.hostel.services import HostelService
from apps.rbac.permissions import require_permission


class HostelListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("hostel.view")]
    serializer_class = HostelSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("hostel.change")()]
        return super().get_permissions()

    def get_queryset(self):
        return HostelService.hostel_queryset(self.request.user)

    def perform_create(self, serializer):
        set_audit_context(actor=self.request.user, branch=getattr(self.request, "branch", None))
        serializer.save()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=status.HTTP_201_CREATED)


class HostelRoomListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("hostel.view")]
    serializer_class = HostelRoomSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("hostel.change")()]
        return super().get_permissions()

    def get_queryset(self):
        qs = HostelService.room_queryset(self.request.user)
        hostel_id = self.request.query_params.get("hostel_id")
        if hostel_id:
            qs = qs.filter(hostel_id=hostel_id)
        return qs.order_by("floor", "room_number")

    def perform_create(self, serializer):
        set_audit_context(actor=self.request.user, branch=getattr(self.request, "branch", None))
        serializer.save()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=status.HTTP_201_CREATED)


class RoomAssignmentListView(generics.ListAPIView):
    permission_classes = [require_permission("hostel.view")]
    serializer_class = RoomAssignmentSerializer

    def get_queryset(self):
        qs = HostelService.assignment_queryset(self.request.user).filter(status="ACTIVE")
        leave_status = self.request.query_params.get("leave_status")
        if leave_status:
            qs = qs.filter(leave_status=leave_status)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})


class RoomAssignmentCreateView(APIView):
    permission_classes = [require_permission("hostel.change")]

    def post(self, request):
        serializer = RoomAssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        room = generics.get_object_or_404(HostelRoom, id=data["room_id"], is_deleted=False)
        student = generics.get_object_or_404(User, id=data["student_id"])
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        try:
            assignment = HostelService.assign_student(room, student, data["check_in"])
        except DomainError as exc:
            return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        return Response({"success": True, "data": RoomAssignmentSerializer(assignment).data}, status=201)


class LeaveStatusUpdateView(APIView):
    permission_classes = [require_permission("hostel.change")]

    def patch(self, request, id):
        assignment = generics.get_object_or_404(RoomAssignment, id=id, is_deleted=False)
        serializer = LeaveStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        assignment = HostelService.update_leave_status(assignment, serializer.validated_data["leave_status"])
        return Response({"success": True, "data": RoomAssignmentSerializer(assignment).data})


class HostelOccupancyMapView(APIView):
    permission_classes = [require_permission("hostel.view")]

    def get(self, request):
        hostel_id = request.query_params.get("hostel_id")
        data = HostelService.occupancy_map(request.user, hostel_id=hostel_id)
        return Response({"success": True, "data": data})


class WardenPortalView(APIView):
    permission_classes = [require_permission("hostel.view")]

    def get(self, request):
        return Response({"success": True, "data": HostelService.warden_portal(request.user)})
