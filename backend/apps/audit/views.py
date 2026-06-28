from rest_framework import generics

from apps.audit.models import AuditLog, AuthenticationEvent
from apps.audit.serializers import AuditLogSerializer, AuthenticationEventSerializer
from apps.rbac.permissions import require_permission


class AuditLogListView(generics.ListAPIView):
    permission_classes = [require_permission("audit.view")]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("actor", "branch").order_by("-occurred_at")
    filterset_fields = ["entity_type", "entity_id", "action", "actor_id", "branch_id"]
    search_fields = ["entity_repr", "entity_type"]


class AuthenticationEventListView(generics.ListAPIView):
    permission_classes = [require_permission("audit.view")]
    serializer_class = AuthenticationEventSerializer
    queryset = AuthenticationEvent.objects.select_related("user", "branch").order_by("-occurred_at")
    filterset_fields = ["event_type", "outcome", "user_id", "branch_id"]
    search_fields = ["email_attempted", "failure_reason"]
