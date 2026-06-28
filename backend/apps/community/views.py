from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.models import (
    CommunityEvent,
    ContentFlag,
    EventStatus,
    ForumCategory,
    ForumPost,
    ForumThread,
    ModerationStatus,
)
from apps.community.serializers import (
    CommunityEventSerializer,
    ContentFlagSerializer,
    EventRsvpSerializer,
    FlagCreateSerializer,
    ForumCategorySerializer,
    ForumPostCreateSerializer,
    ForumPostSerializer,
    ForumThreadCreateSerializer,
    ForumThreadSerializer,
    ModerationSerializer,
)
from apps.community.services import EventService, FlagService, ForumService
from apps.core.branch_scope import branch_scoped_queryset
from apps.core.context import set_audit_context
from apps.core.exceptions import DomainError
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService


def _can_moderate(user):
    return PermissionService.user_has_permission(user, "community.moderate")


class CommunityEventListCreateView(generics.ListCreateAPIView):
    serializer_class = CommunityEventSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("community.change")()]
        return [require_permission("community.view")()]

    def get_queryset(self):
        qs = CommunityEvent.objects.filter(is_deleted=False).select_related("branch")
        if self.request.method == "GET":
            qs = qs.filter(status=EventStatus.PUBLISHED, starts_at__gte=timezone.now())
            user = self.request.user
            if not PermissionService.user_has_super_admin(user):
                branch_ids = user.branch_memberships.filter(is_active=True, is_deleted=False).values_list(
                    "branch_id", flat=True
                )
                qs = qs.filter(Q(is_global=True) | Q(branch_id__in=branch_ids))
        else:
            qs = branch_scoped_queryset(self.request.user, qs)
        return qs.order_by("starts_at")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def perform_create(self, serializer):
        set_audit_context(actor=self.request.user, branch=getattr(self.request, "branch", None))
        serializer.save(created_by=self.request.user, status=EventStatus.PUBLISHED)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=status.HTTP_201_CREATED)


class EventRsvpView(APIView):
    permission_classes = [require_permission("community.add")]

    def post(self, request, id):
        event = generics.get_object_or_404(CommunityEvent, id=id, is_deleted=False, status=EventStatus.PUBLISHED)
        serializer = EventRsvpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rsvp = EventService.rsvp(event, request.user, serializer.validated_data["status"], serializer.validated_data.get("notes", ""))
        except DomainError as exc:
            return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        return Response({"success": True, "data": {"status": rsvp.status}})


class ForumCategoryListView(generics.ListAPIView):
    permission_classes = [require_permission("community.view")]
    serializer_class = ForumCategorySerializer

    def get_queryset(self):
        return ForumCategory.objects.filter(is_active=True, is_deleted=False).order_by("name")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class ForumThreadListCreateView(generics.ListCreateAPIView):
    serializer_class = ForumThreadSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("community.add")()]
        return [require_permission("community.view")()]

    def get_queryset(self):
        if self.request.method == "GET":
            return ForumService.visible_threads_qs(self.request.user)
        return ForumThread.objects.filter(is_deleted=False).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = ForumThreadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        category = generics.get_object_or_404(ForumCategory, id=data["category_id"], is_active=True)
        auto = _can_moderate(request.user)
        thread = ForumService.create_thread(category, request.user, data["title"], data["body"], auto_approve=auto)
        return Response(
            {"success": True, "data": ForumThreadSerializer(thread).data},
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})


class ForumThreadDetailView(APIView):
    permission_classes = [require_permission("community.view")]

    def get(self, request, id):
        thread = generics.get_object_or_404(ForumThread, id=id, is_deleted=False, moderation_status=ModerationStatus.APPROVED)
        posts = ForumService.visible_posts_qs(thread)
        return Response({
            "success": True,
            "data": {
                "thread": ForumThreadSerializer(thread).data,
                "posts": ForumPostSerializer(posts, many=True).data,
            },
        })


class ForumPostCreateView(APIView):
    permission_classes = [require_permission("community.add")]

    def post(self, request, id):
        thread = generics.get_object_or_404(ForumThread, id=id, is_deleted=False)
        serializer = ForumPostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auto = _can_moderate(request.user)
        try:
            post = ForumService.create_post(thread, request.user, serializer.validated_data["body"], auto_approve=auto)
        except DomainError as exc:
            return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        return Response({"success": True, "data": ForumPostSerializer(post).data}, status=201)


class ForumThreadFlagView(APIView):
    permission_classes = [require_permission("community.add")]

    def post(self, request, id):
        thread = generics.get_object_or_404(ForumThread, id=id, is_deleted=False)
        serializer = FlagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            flag = FlagService.flag_thread(thread, request.user, serializer.validated_data["reason"])
        except DomainError as exc:
            return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        return Response({"success": True, "data": ContentFlagSerializer(flag).data}, status=201)


class ForumPostFlagView(APIView):
    permission_classes = [require_permission("community.add")]

    def post(self, request, thread_id, id):
        post = generics.get_object_or_404(ForumPost, id=id, thread_id=thread_id, is_deleted=False)
        serializer = FlagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            flag = FlagService.flag_post(post, request.user, serializer.validated_data["reason"])
        except DomainError as exc:
            return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        return Response({"success": True, "data": ContentFlagSerializer(flag).data}, status=201)


class ModerationQueueView(APIView):
    permission_classes = [require_permission("community.moderate")]

    def get(self, request):
        threads = ForumThread.objects.filter(
            is_deleted=False, moderation_status=ModerationStatus.PENDING
        ).select_related("category", "author")[:50]
        posts = ForumPost.objects.filter(
            is_deleted=False, moderation_status=ModerationStatus.PENDING
        ).select_related("thread", "author")[:50]
        flags = ContentFlag.objects.filter(status="OPEN").select_related("thread", "post", "flagged_by")[:50]
        return Response({
            "success": True,
            "data": {
                "threads": ForumThreadSerializer(threads, many=True).data,
                "posts": ForumPostSerializer(posts, many=True).data,
                "flags": ContentFlagSerializer(flags, many=True).data,
            },
        })


class ForumThreadModerateView(APIView):
    permission_classes = [require_permission("community.moderate")]

    def patch(self, request, id):
        thread = generics.get_object_or_404(ForumThread, id=id, is_deleted=False)
        serializer = ModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        thread = ForumService.moderate_thread(
            thread, request.user, serializer.validated_data["moderation_status"], serializer.validated_data.get("moderation_note", "")
        )
        return Response({"success": True, "data": ForumThreadSerializer(thread).data})


class ForumPostModerateView(APIView):
    permission_classes = [require_permission("community.moderate")]

    def patch(self, request, id):
        post = generics.get_object_or_404(ForumPost, id=id, is_deleted=False)
        serializer = ModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        post = ForumService.moderate_post(
            post, request.user, serializer.validated_data["moderation_status"], serializer.validated_data.get("moderation_note", "")
        )
        return Response({"success": True, "data": ForumPostSerializer(post).data})
