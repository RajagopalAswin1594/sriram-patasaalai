from django.db import transaction
from django.utils import timezone

from apps.admissions.models import ApplicationStatus, ApplicationStatusHistory, PaymentStatus
from apps.admissions.notifications import NotificationService
from apps.admissions.state_machine import assert_review_decision, assert_transition, is_reviewable, normalize_review_status
from apps.core.exceptions import ConflictError, DomainError


class ReviewWorkflowService:
    @staticmethod
    def record_status_change(application, from_status, to_status, actor=None, reason="", metadata=None):
        ApplicationStatusHistory.objects.create(
            application=application,
            from_status=from_status,
            to_status=to_status,
            changed_by=actor,
            reason=reason,
            metadata=metadata or {},
        )

    @classmethod
    @transaction.atomic
    def transition(cls, application, to_status, actor=None, reason="", metadata=None):
        from_status = normalize_review_status(application.status)
        to_status = normalize_review_status(to_status)
        assert_transition(from_status, to_status)

        if from_status == to_status:
            return application

        application.status = to_status
        application.save(update_fields=["status", "updated_at"])

        cls.record_status_change(application, from_status, to_status, actor=actor, reason=reason, metadata=metadata)
        return application

    @classmethod
    @transaction.atomic
    def mark_pending_review(cls, application, actor=None):
        """Called after payment — moves application into Pending review queue."""
        payment = getattr(application, "payment", None)
        if not payment or payment.status != PaymentStatus.COMPLETED:
            raise ConflictError("Payment must be completed before pending review.")

        application = cls.transition(
            application,
            ApplicationStatus.PENDING,
            actor=actor,
            reason="Payment confirmed; awaiting branch admin review.",
        )
        NotificationService.send_application_pending_review(application)
        return application

    @classmethod
    @transaction.atomic
    def approve(cls, application, actor, review_notes=""):
        if not is_reviewable(application.status):
            raise ConflictError("Only pending applications can be approved.")
        payment = getattr(application, "payment", None)
        if not payment or payment.status != PaymentStatus.COMPLETED:
            raise ConflictError("Payment must be completed before approval.")

        application.reviewed_at = timezone.now()
        application.reviewed_by = actor
        application.rejection_reason = ""
        if review_notes:
            application.review_notes = review_notes
        application.save(update_fields=["reviewed_at", "reviewed_by", "rejection_reason", "review_notes", "updated_at"])

        cls.transition(application, ApplicationStatus.APPROVED, actor=actor, reason="Application approved.")
        from apps.admissions.provisioning import AdmissionProvisioningService

        AdmissionProvisioningService.provision_from_application(application, actor)
        NotificationService.send_application_approved(application)
        return application

    @classmethod
    @transaction.atomic
    def reject(cls, application, actor, rejection_reason="", review_notes=""):
        if not is_reviewable(application.status):
            raise ConflictError("Only pending applications can be rejected.")
        payment = getattr(application, "payment", None)
        if not payment or payment.status != PaymentStatus.COMPLETED:
            raise ConflictError("Payment must be completed before rejection.")

        application.reviewed_at = timezone.now()
        application.reviewed_by = actor
        application.rejection_reason = rejection_reason
        if review_notes:
            application.review_notes = review_notes
        application.save(
            update_fields=["reviewed_at", "reviewed_by", "rejection_reason", "review_notes", "updated_at"]
        )

        cls.transition(
            application,
            ApplicationStatus.REJECTED,
            actor=actor,
            reason=rejection_reason or "Application rejected.",
        )
        NotificationService.send_application_rejected(application)
        return application

    @classmethod
    @transaction.atomic
    def assign_reviewer(cls, application, reviewer, actor):
        if not is_reviewable(application.status):
            raise ConflictError("Can only assign reviewer to pending applications.")
        application.assigned_to = reviewer
        application.save(update_fields=["assigned_to", "updated_at"])
        cls.record_status_change(
            application,
            application.status,
            application.status,
            actor=actor,
            reason=f"Assigned to {reviewer.email}",
            metadata={"assigned_to": str(reviewer.id)},
        )
        return application

    @classmethod
    def get_stale_pending_applications(cls, days=7):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        from apps.admissions.models import AdmissionApplication

        return AdmissionApplication.objects.filter(
            status__in=[ApplicationStatus.PENDING, "UNDER_REVIEW"],
            submitted_at__lt=cutoff,
            is_deleted=False,
        )
