from django.utils import timezone

from apps.gurukulam_feedback.models import GurukulamFeedback, GurukulamFeedbackHistory, GurukulamFeedbackStatus


class GurukulamFeedbackService:
    @classmethod
    def record_history(cls, feedback, from_status, to_status, actor=None, reason=""):
        GurukulamFeedbackHistory.objects.create(
            feedback=feedback,
            from_status=from_status or "",
            to_status=to_status,
            changed_by=actor,
            reason=reason,
        )

    @classmethod
    def submit(cls, feedback: GurukulamFeedback, actor=None):
        cls.record_history(feedback, "", GurukulamFeedbackStatus.SUBMITTED, actor, "Feedback submitted")
        return feedback

    @classmethod
    def update_status(cls, feedback: GurukulamFeedback, new_status: str, actor, reason="", admin_response=""):
        old = feedback.status
        feedback.status = new_status
        update_fields = ["status", "updated_at"]
        if admin_response:
            feedback.admin_response = admin_response
            feedback.responded_by = actor
            feedback.responded_at = timezone.now()
            update_fields.extend(["admin_response", "responded_by", "responded_at"])
        feedback.save(update_fields=update_fields)
        cls.record_history(feedback, old, new_status, actor, reason or admin_response[:200])
        return feedback
