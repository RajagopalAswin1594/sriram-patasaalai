from django.db import transaction
from django.utils import timezone

from apps.admissions.models import (
    ApplicationDocumentReviewLog,
    ApplicationStatus,
    DocumentUploadStatus,
)
from apps.admissions.notifications import NotificationService
from apps.core.exceptions import ConflictError, DomainError


class DocumentReviewAction:
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_RESUBMIT = "REQUEST_RESUBMIT"

    CHOICES = (APPROVE, REJECT, REQUEST_RESUBMIT)


ACTION_TO_STATUS = {
    DocumentReviewAction.APPROVE: DocumentUploadStatus.VERIFIED,
    DocumentReviewAction.REJECT: DocumentUploadStatus.REJECTED,
    DocumentReviewAction.REQUEST_RESUBMIT: DocumentUploadStatus.RESUBMIT_REQUESTED,
}


class DocumentReviewService:
    @staticmethod
    def application_allows_document_review(application) -> bool:
        return application.status in (
            ApplicationStatus.PENDING,
            ApplicationStatus.UNDER_REVIEW,
        )

    @classmethod
    @transaction.atomic
    def review(cls, document, action: str, actor, reason: str = "", channels: list[str] | None = None):
        if action not in DocumentReviewAction.CHOICES:
            raise DomainError("Invalid document review action.")

        application = document.application
        if not cls.application_allows_document_review(application):
            raise ConflictError("Documents can only be reviewed while the application is pending.")

        if document.upload_status != DocumentUploadStatus.UPLOADED:
            raise ConflictError("Only uploaded documents awaiting review can be actioned.")

        if action in (DocumentReviewAction.REJECT, DocumentReviewAction.REQUEST_RESUBMIT) and not reason.strip():
            raise DomainError("A reason is required when rejecting or requesting resubmission.")

        from_status = document.upload_status
        to_status = ACTION_TO_STATUS[action]

        document.upload_status = to_status
        document.review_notes = reason.strip()
        document.reviewed_by = actor
        document.reviewed_at = timezone.now()
        document.save(
            update_fields=["upload_status", "review_notes", "reviewed_by", "reviewed_at", "updated_at"],
        )

        selected_channels = channels or ["EMAIL", "SMS", "WHATSAPP"]
        ApplicationDocumentReviewLog.objects.create(
            document=document,
            application=application,
            action=action,
            from_status=from_status,
            to_status=to_status,
            changed_by=actor,
            reason=reason.strip(),
            notified_channels=selected_channels,
        )

        NotificationService.send_document_review(document, action, reason.strip(), selected_channels)
        return document
