from django.urls import path

from apps.community.views import (
    CommunityEventListCreateView,
    EventRsvpView,
    ForumCategoryListView,
    ForumPostCreateView,
    ForumPostFlagView,
    ForumPostModerateView,
    ForumThreadDetailView,
    ForumThreadFlagView,
    ForumThreadListCreateView,
    ForumThreadModerateView,
    ModerationQueueView,
)

urlpatterns = [
    path("community/events/", CommunityEventListCreateView.as_view()),
    path("community/events/<uuid:id>/rsvp/", EventRsvpView.as_view()),
    path("community/forum/categories/", ForumCategoryListView.as_view()),
    path("community/forum/threads/", ForumThreadListCreateView.as_view()),
    path("community/forum/threads/<uuid:id>/", ForumThreadDetailView.as_view()),
    path("community/forum/threads/<uuid:id>/posts/", ForumPostCreateView.as_view()),
    path("community/forum/threads/<uuid:id>/flag/", ForumThreadFlagView.as_view()),
    path("community/forum/threads/<uuid:thread_id>/posts/<uuid:id>/flag/", ForumPostFlagView.as_view()),
    path("community/moderation/queue/", ModerationQueueView.as_view()),
    path("community/moderation/threads/<uuid:id>/", ForumThreadModerateView.as_view()),
    path("community/moderation/posts/<uuid:id>/", ForumPostModerateView.as_view()),
]
