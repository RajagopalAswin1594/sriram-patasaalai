from django.urls import path

from apps.feedback.views import (
    FeedbackApproveGitHubView,
    FeedbackCommentCreateView,
    FeedbackDetailView,
    FeedbackGitHubTestView,
    FeedbackIntegrationsView,
    FeedbackListView,
    FeedbackStatsView,
    FeedbackStatusUpdateView,
    FeedbackSubmitView,
)

urlpatterns = [
    path("feedback/submit/", FeedbackSubmitView.as_view()),
    path("feedback/", FeedbackListView.as_view()),
    path("feedback/stats/", FeedbackStatsView.as_view()),
    path("feedback/integrations/", FeedbackIntegrationsView.as_view()),
    path("feedback/integrations/test-github/", FeedbackGitHubTestView.as_view()),
    path("feedback/<uuid:id>/", FeedbackDetailView.as_view()),
    path("feedback/<uuid:id>/approve-github/", FeedbackApproveGitHubView.as_view()),
    path("feedback/<uuid:id>/status/", FeedbackStatusUpdateView.as_view()),
    path("feedback/<uuid:id>/comments/", FeedbackCommentCreateView.as_view()),
]
