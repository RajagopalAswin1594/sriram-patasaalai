from django.urls import path

from apps.notifications.views import (
    NotificationLogListView,
    NotificationTemplateDetailView,
    NotificationTemplateListCreateView,
    NotificationTestSendView,
)

urlpatterns = [
    path("notifications/templates/", NotificationTemplateListCreateView.as_view()),
    path("notifications/templates/<uuid:id>/", NotificationTemplateDetailView.as_view()),
    path("notifications/logs/", NotificationLogListView.as_view()),
    path("notifications/test-send/", NotificationTestSendView.as_view()),
]
