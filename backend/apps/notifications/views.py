from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import set_audit_context
from apps.notifications.models import NotificationLog, NotificationTemplate
from apps.notifications.serializers import (
    NotificationLogSerializer,
    NotificationTemplateSerializer,
    NotificationTestSendSerializer,
)
from apps.notifications.services import NotificationDispatcher
from apps.rbac.permissions import require_permission


class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("notifications.view")]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.filter(is_deleted=False).order_by("code")

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("notifications.change")()]
        return super().get_permissions()

    def perform_create(self, serializer):
        set_audit_context(actor=self.request.user, branch=getattr(self.request, "branch", None))
        serializer.save()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=status.HTTP_201_CREATED)


class NotificationTemplateDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [require_permission("notifications.view")]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.filter(is_deleted=False)
    lookup_field = "id"

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [require_permission("notifications.change")()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def update(self, request, *args, **kwargs):
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        response = super().update(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class NotificationLogListView(generics.ListAPIView):
    permission_classes = [require_permission("notifications.view")]
    serializer_class = NotificationLogSerializer
    queryset = NotificationLog.objects.all().order_by("-created_at")[:200]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class NotificationTestSendView(APIView):
    permission_classes = [require_permission("notifications.change")]

    def post(self, request):
        serializer = NotificationTestSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        results = NotificationDispatcher.send(
            template_code=data["template_code"],
            recipient_email=data.get("recipient_email", ""),
            recipient_phone=data.get("recipient_phone", ""),
            context=data.get("context", {}),
            idempotency_key=data.get("idempotency_key", ""),
            user=request.user,
        )
        return Response({"success": True, "data": results})
