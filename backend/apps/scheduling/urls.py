from django.urls import path

from apps.scheduling.views import (
    AcharyaMappingView,
    AcharyaPortalView,
    AcharyaRegisterView,
    TeachingSessionListCreateView,
)

urlpatterns = [
    path("scheduling/sessions/", TeachingSessionListCreateView.as_view(), name="teaching-session-list"),
    path("scheduling/acharyas/register/", AcharyaRegisterView.as_view(), name="acharya-register"),
    path("scheduling/acharyas/portal/", AcharyaPortalView.as_view(), name="acharya-portal"),
    path("scheduling/acharyas/mapping/", AcharyaMappingView.as_view(), name="acharya-mapping"),
]
