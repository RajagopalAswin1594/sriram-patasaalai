from django.urls import path

from apps.gurukulam_feedback.views import (
    GurukulamFeedbackDetailView,
    GurukulamFeedbackListView,
    GurukulamFeedbackStatsView,
    GurukulamFeedbackStatusUpdateView,
    GurukulamFeedbackSubmitView,
)

urlpatterns = [
    path("gurukulam-feedback/submit/", GurukulamFeedbackSubmitView.as_view()),
    path("gurukulam-feedback/", GurukulamFeedbackListView.as_view()),
    path("gurukulam-feedback/stats/", GurukulamFeedbackStatsView.as_view()),
    path("gurukulam-feedback/<uuid:id>/", GurukulamFeedbackDetailView.as_view()),
    path("gurukulam-feedback/<uuid:id>/status/", GurukulamFeedbackStatusUpdateView.as_view()),
]
