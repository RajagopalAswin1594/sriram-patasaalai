from django.db import models

from apps.core.models import AuditableModel


class EventStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    CANCELLED = "CANCELLED", "Cancelled"


class RsvpStatus(models.TextChoices):
    GOING = "GOING", "Going"
    INTERESTED = "INTERESTED", "Interested"
    CANCELLED = "CANCELLED", "Cancelled"


class ModerationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    HIDDEN = "HIDDEN", "Hidden"
    REJECTED = "REJECTED", "Rejected"


class FlagStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    REVIEWED = "REVIEWED", "Reviewed"
    DISMISSED = "DISMISSED", "Dismissed"


class FlagContentType(models.TextChoices):
    FORUM_THREAD = "FORUM_THREAD", "Forum Thread"
    FORUM_POST = "FORUM_POST", "Forum Post"


class CommunityEvent(AuditableModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.DRAFT)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="events_created")
    is_global = models.BooleanField(default=False)

    class Meta:
        ordering = ["starts_at"]
        indexes = [models.Index(fields=["status", "starts_at"])]


class EventRSVP(AuditableModel):
    event = models.ForeignKey(CommunityEvent, on_delete=models.CASCADE, related_name="rsvps")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="event_rsvps")
    status = models.CharField(max_length=20, choices=RsvpStatus.choices, default=RsvpStatus.GOING)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "user"], name="unique_rsvp_per_user_event"),
        ]


class ForumCategory(AuditableModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]


class ForumThread(AuditableModel):
    category = models.ForeignKey(ForumCategory, on_delete=models.PROTECT, related_name="threads")
    author = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="forum_threads")
    title = models.CharField(max_length=255)
    body = models.TextField()
    moderation_status = models.CharField(
        max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING
    )
    moderation_note = models.TextField(blank=True)
    moderated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="forum_threads_moderated",
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    flag_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["moderation_status", "created_at"])]


class ForumPost(AuditableModel):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="forum_posts")
    body = models.TextField()
    moderation_status = models.CharField(
        max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING
    )
    moderation_note = models.TextField(blank=True)
    moderated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="forum_posts_moderated",
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    flag_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["created_at"]


class ContentFlag(AuditableModel):
    content_type = models.CharField(max_length=20, choices=FlagContentType.choices)
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, null=True, blank=True, related_name="flags")
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name="flags")
    flagged_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="content_flags")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=FlagStatus.choices, default=FlagStatus.OPEN)
    reviewed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="content_flags_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "thread", "flagged_by"],
                condition=models.Q(thread__isnull=False),
                name="unique_thread_flag_per_user",
            ),
            models.UniqueConstraint(
                fields=["content_type", "post", "flagged_by"],
                condition=models.Q(post__isnull=False),
                name="unique_post_flag_per_user",
            ),
        ]
