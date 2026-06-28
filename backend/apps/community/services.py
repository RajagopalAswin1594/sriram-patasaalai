from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import DomainError
from apps.community.models import (
    ContentFlag,
    EventRSVP,
    FlagContentType,
    ForumPost,
    ForumThread,
    ModerationStatus,
    RsvpStatus,
)


FLAG_AUTO_HIDE_THRESHOLD = 3


class EventService:
    @classmethod
    @transaction.atomic
    def rsvp(cls, event, user, status=RsvpStatus.GOING, notes=""):
        if status == RsvpStatus.GOING and event.capacity:
            going_count = EventRSVP.objects.filter(
                event=event, status=RsvpStatus.GOING, is_deleted=False
            ).exclude(user=user).count()
            if going_count >= event.capacity:
                raise DomainError("Event is at full capacity.")

        rsvp, _ = EventRSVP.objects.update_or_create(
            event=event,
            user=user,
            defaults={"status": status, "notes": notes},
        )
        return rsvp


class ForumService:
    @classmethod
    def visible_threads_qs(cls, user=None):
        qs = ForumThread.objects.filter(is_deleted=False, moderation_status=ModerationStatus.APPROVED)
        return qs.select_related("category", "author", "author__profile")

    @classmethod
    def visible_posts_qs(cls, thread):
        return ForumPost.objects.filter(
            thread=thread, is_deleted=False, moderation_status=ModerationStatus.APPROVED
        ).select_related("author", "author__profile")

    @classmethod
    @transaction.atomic
    def create_thread(cls, category, author, title, body, auto_approve=False):
        status = ModerationStatus.APPROVED if auto_approve else ModerationStatus.PENDING
        return ForumThread.objects.create(
            category=category,
            author=author,
            title=title,
            body=body,
            moderation_status=status,
        )

    @classmethod
    @transaction.atomic
    def create_post(cls, thread, author, body, auto_approve=False):
        if thread.moderation_status != ModerationStatus.APPROVED:
            raise DomainError("Cannot reply to a thread that is not approved.")
        status = ModerationStatus.APPROVED if auto_approve else ModerationStatus.PENDING
        return ForumPost.objects.create(
            thread=thread,
            author=author,
            body=body,
            moderation_status=status,
        )

    @classmethod
    @transaction.atomic
    def moderate_thread(cls, thread, moderator, status, note=""):
        thread.moderation_status = status
        thread.moderation_note = note
        thread.moderated_by = moderator
        thread.moderated_at = timezone.now()
        thread.save(update_fields=["moderation_status", "moderation_note", "moderated_by", "moderated_at", "updated_at"])
        return thread

    @classmethod
    @transaction.atomic
    def moderate_post(cls, post, moderator, status, note=""):
        post.moderation_status = status
        post.moderation_note = note
        post.moderated_by = moderator
        post.moderated_at = timezone.now()
        post.save(update_fields=["moderation_status", "moderation_note", "moderated_by", "moderated_at", "updated_at"])
        return post


class FlagService:
    @classmethod
    @transaction.atomic
    def flag_thread(cls, thread, user, reason):
        flag, created = ContentFlag.objects.get_or_create(
            content_type=FlagContentType.FORUM_THREAD,
            thread=thread,
            flagged_by=user,
            defaults={"reason": reason},
        )
        if not created:
            raise DomainError("You have already flagged this thread.")
        thread.flag_count = ContentFlag.objects.filter(thread=thread, is_deleted=False).count()
        thread.save(update_fields=["flag_count", "updated_at"])
        if thread.flag_count >= FLAG_AUTO_HIDE_THRESHOLD:
            ForumService.moderate_thread(thread, user, ModerationStatus.HIDDEN, "Auto-hidden due to multiple flags.")
        return flag

    @classmethod
    @transaction.atomic
    def flag_post(cls, post, user, reason):
        flag, created = ContentFlag.objects.get_or_create(
            content_type=FlagContentType.FORUM_POST,
            post=post,
            flagged_by=user,
            defaults={"reason": reason},
        )
        if not created:
            raise DomainError("You have already flagged this post.")
        post.flag_count = ContentFlag.objects.filter(post=post, is_deleted=False).count()
        post.save(update_fields=["flag_count", "updated_at"])
        if post.flag_count >= FLAG_AUTO_HIDE_THRESHOLD:
            ForumService.moderate_post(post, user, ModerationStatus.HIDDEN, "Auto-hidden due to multiple flags.")
        return flag

    @classmethod
    @transaction.atomic
    def review_flag(cls, flag, reviewer, status):
        flag.status = status
        flag.reviewed_by = reviewer
        flag.reviewed_at = timezone.now()
        flag.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
        return flag
