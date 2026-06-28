from rest_framework import serializers

from apps.community.models import (
    CommunityEvent,
    ContentFlag,
    EventRSVP,
    ForumCategory,
    ForumPost,
    ForumThread,
)


class CommunityEventSerializer(serializers.ModelSerializer):
    rsvp_count = serializers.SerializerMethodField()
    user_rsvp = serializers.SerializerMethodField()
    branch_code = serializers.CharField(source="branch.code", read_only=True, allow_null=True)

    class Meta:
        model = CommunityEvent
        fields = (
            "id",
            "branch_id",
            "branch_code",
            "title",
            "description",
            "location",
            "starts_at",
            "ends_at",
            "capacity",
            "status",
            "is_global",
            "rsvp_count",
            "user_rsvp",
            "created_at",
        )
        read_only_fields = ("status",)

    def get_rsvp_count(self, obj):
        return obj.rsvps.filter(status="GOING", is_deleted=False).count()

    def get_user_rsvp(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        rsvp = obj.rsvps.filter(user=request.user, is_deleted=False).first()
        return rsvp.status if rsvp else None


class EventRsvpSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["GOING", "INTERESTED", "CANCELLED"], default="GOING")
    notes = serializers.CharField(required=False, allow_blank=True, max_length=255)


class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = ("id", "code", "name", "description", "branch_id", "is_active")


class ForumThreadSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumThread
        fields = (
            "id",
            "category_id",
            "category_name",
            "author_id",
            "author_name",
            "title",
            "body",
            "moderation_status",
            "flag_count",
            "post_count",
            "created_at",
        )
        read_only_fields = ("moderation_status", "flag_count")

    def get_author_name(self, obj):
        return getattr(obj.author.profile, "display_name", obj.author.email)

    def get_post_count(self, obj):
        return obj.posts.filter(is_deleted=False, moderation_status="APPROVED").count()


class ForumThreadCreateSerializer(serializers.Serializer):
    category_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()


class ForumPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        fields = (
            "id",
            "thread_id",
            "author_id",
            "author_name",
            "body",
            "moderation_status",
            "flag_count",
            "created_at",
        )

    def get_author_name(self, obj):
        return getattr(obj.author.profile, "display_name", obj.author.email)


class ForumPostCreateSerializer(serializers.Serializer):
    body = serializers.CharField()


class ContentFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentFlag
        fields = ("id", "content_type", "thread_id", "post_id", "reason", "status", "created_at")


class FlagCreateSerializer(serializers.Serializer):
    reason = serializers.CharField()


class ModerationSerializer(serializers.Serializer):
    moderation_status = serializers.ChoiceField(choices=["APPROVED", "HIDDEN", "REJECTED"])
    moderation_note = serializers.CharField(required=False, allow_blank=True)
