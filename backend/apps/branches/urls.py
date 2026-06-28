from django.urls import path

from apps.branches.views import (
    BranchDetailView,
    BranchListCreateView,
    SetPrimaryBranchView,
    UserBranchMembershipDetailView,
    UserBranchMembershipListCreateView,
)

urlpatterns = [
    path("branches/", BranchListCreateView.as_view(), name="branch-list-create"),
    path("branches/<uuid:id>/", BranchDetailView.as_view(), name="branch-detail"),
    path("branch-memberships/", UserBranchMembershipListCreateView.as_view(), name="branch-membership-list-create"),
    path("branch-memberships/<uuid:id>/", UserBranchMembershipDetailView.as_view(), name="branch-membership-detail"),
    path(
        "users/<uuid:user_id>/branches/<uuid:branch_id>/set-primary/",
        SetPrimaryBranchView.as_view(),
        name="set-primary-branch",
    ),
]
