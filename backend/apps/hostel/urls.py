from django.urls import path

from apps.hostel.views import (
    HostelListCreateView,
    HostelOccupancyMapView,
    HostelRoomListCreateView,
    LeaveStatusUpdateView,
    RoomAssignmentCreateView,
    RoomAssignmentListView,
    WardenPortalView,
)

urlpatterns = [
    path("hostel/hostels/", HostelListCreateView.as_view()),
    path("hostel/rooms/", HostelRoomListCreateView.as_view()),
    path("hostel/assignments/", RoomAssignmentListView.as_view()),
    path("hostel/assignments/create/", RoomAssignmentCreateView.as_view()),
    path("hostel/assignments/<uuid:id>/leave/", LeaveStatusUpdateView.as_view()),
    path("hostel/occupancy/", HostelOccupancyMapView.as_view()),
    path("hostel/warden-portal/", WardenPortalView.as_view()),
]
