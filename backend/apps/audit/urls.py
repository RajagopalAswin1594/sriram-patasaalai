from django.urls import path

from apps.audit.views import AuditLogListView, AuthenticationEventListView

urlpatterns = [
    path("audit/logs/", AuditLogListView.as_view(), name="audit-log-list"),
    path("audit/auth-events/", AuthenticationEventListView.as_view(), name="auth-event-list"),
]
