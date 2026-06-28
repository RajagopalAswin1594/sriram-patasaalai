import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.admissions.models import (
    ApplicationNotification,
    DocumentType,
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
)

logger = logging.getLogger(__name__)

DOCUMENT_TYPE_LABELS = dict(DocumentType.choices)


class NotificationService:
    @classmethod
    def _create_log(cls, application, channel, event_type, recipient, status, error_message=""):
        return ApplicationNotification.objects.create(
            application=application,
            channel=channel,
            event_type=event_type,
            recipient=recipient,
            status=status,
            error_message=error_message,
            sent_at=timezone.now() if status == NotificationStatus.SENT else None,
        )

    @classmethod
    def send_application_pending_review(cls, application):
        """Notify parent that application is received and pending review."""
        cls._dispatch(
            application,
            NotificationEventType.APPLICATION_PENDING,
            subject=f"Application Received – {application.application_number}",
            message=(
                f"Dear {application.parent_name},\n\n"
                f"We have received the admission application for {application.student_first_name} "
                f"({application.application_number}). It is now pending review by our team.\n\n"
                f"– {application.branch.name}"
            ),
        )

    @classmethod
    def send_application_approved(cls, application):
        cls._dispatch(
            application,
            NotificationEventType.APPLICATION_APPROVED,
            subject=f"Application Approved – {application.application_number}",
            message=(
                f"Dear {application.parent_name},\n\n"
                f"Congratulations! The application for {application.student_first_name} "
                f"({application.application_number}) has been approved.\n\n"
                f"Our team will contact you at {application.parent_phone} with next steps.\n\n"
                f"– {application.branch.name}"
            ),
        )

    @classmethod
    def send_application_rejected(cls, application):
        reason = application.rejection_reason or "Please contact the branch for details."
        cls._dispatch(
            application,
            NotificationEventType.APPLICATION_REJECTED,
            subject=f"Application Update – {application.application_number}",
            message=(
                f"Dear {application.parent_name},\n\n"
                f"Regarding application {application.application_number} for {application.student_first_name}:\n"
                f"{reason}\n\n"
                f"– {application.branch.name}"
            ),
        )

    @classmethod
    def send_document_review(cls, document, action: str, reason: str, channels: list[str]):
        application = document.application
        doc_label = DOCUMENT_TYPE_LABELS.get(document.document_type, document.document_type)
        apply_url = getattr(settings, "PUBLIC_APP_BASE_URL", "http://localhost:3000/apply")

        if action == "APPROVE":
            event_type = NotificationEventType.DOCUMENT_VERIFIED
            subject = f"Document Verified – {application.application_number}"
            message = (
                f"Dear {application.parent_name},\n\n"
                f"Your submitted document ({doc_label}) for application {application.application_number} "
                f"has been verified.\n\n"
                f"– {application.branch.name}"
            )
        elif action == "REJECT":
            event_type = NotificationEventType.DOCUMENT_REJECTED
            subject = f"Document Rejected – {application.application_number}"
            message = (
                f"Dear {application.parent_name},\n\n"
                f"Your submitted document ({doc_label}) for application {application.application_number} "
                f"could not be accepted.\n\n"
                f"Reason: {reason}\n\n"
                f"Please contact {application.branch.name} for assistance.\n\n"
                f"– {application.branch.name}"
            )
        else:
            event_type = NotificationEventType.DOCUMENT_RESUBMIT_REQUESTED
            subject = f"Document Resubmission Required – {application.application_number}"
            message = (
                f"Dear {application.parent_name},\n\n"
                f"Please resubmit the document ({doc_label}) for application {application.application_number}.\n\n"
                f"Reason: {reason}\n\n"
                f"Visit {apply_url} to upload the corrected document.\n\n"
                f"– {application.branch.name}"
            )

        cls._dispatch(application, event_type, subject, message, channels=channels)

    @classmethod
    def _dispatch(cls, application, event_type, subject, message, channels: list[str] | None = None):
        selected = set(channels or ["EMAIL", "SMS", "WHATSAPP"])
        email = application.parent_email
        phone = application.parent_phone

        if NotificationChannel.EMAIL in selected and email:
            cls._send_email(application, event_type, email, subject, message)
        elif NotificationChannel.EMAIL in selected and phone:
            logger.info("No email on application %s; skipping email notification.", application.application_number)

        if NotificationChannel.SMS in selected and phone:
            cls._send_sms(application, event_type, phone, message)

        if NotificationChannel.WHATSAPP in selected and phone:
            cls._send_whatsapp(application, event_type, phone, message)

    @classmethod
    def _send_email(cls, application, event_type, recipient, subject, message):
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            cls._create_log(application, NotificationChannel.EMAIL, event_type, recipient, NotificationStatus.SENT)
        except Exception as exc:
            logger.exception("Email notification failed for %s", application.application_number)
            cls._create_log(
                application,
                NotificationChannel.EMAIL,
                event_type,
                recipient,
                NotificationStatus.FAILED,
                error_message=str(exc),
            )

    @classmethod
    def _send_sms(cls, application, event_type, phone, message):
        if not getattr(settings, "SMS_ENABLED", False):
            logger.info(
                "[SMS stub] To=%s App=%s Message=%s",
                phone,
                application.application_number,
                message[:80],
            )
            cls._create_log(application, NotificationChannel.SMS, event_type, phone, NotificationStatus.SENT)
            return

        try:
            import requests

            response = requests.post(
                settings.SMS_API_URL,
                headers={"Authorization": f"Bearer {settings.SMS_API_TOKEN}"},
                json={"to": phone, "message": message},
                timeout=15,
            )
            response.raise_for_status()
            cls._create_log(application, NotificationChannel.SMS, event_type, phone, NotificationStatus.SENT)
        except Exception as exc:
            logger.exception("SMS notification failed for %s", application.application_number)
            cls._create_log(
                application,
                NotificationChannel.SMS,
                event_type,
                phone,
                NotificationStatus.FAILED,
                error_message=str(exc),
            )

    @classmethod
    def _send_whatsapp(cls, application, event_type, phone, message):
        if not getattr(settings, "WHATSAPP_ENABLED", False):
            logger.info(
                "[WhatsApp stub] To=%s App=%s Message=%s",
                phone,
                application.application_number,
                message[:80],
            )
            cls._create_log(application, NotificationChannel.WHATSAPP, event_type, phone, NotificationStatus.SENT)
            return

        try:
            import requests

            response = requests.post(
                settings.WHATSAPP_API_URL,
                headers={"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}"},
                json={"to": phone, "message": message},
                timeout=15,
            )
            response.raise_for_status()
            cls._create_log(application, NotificationChannel.WHATSAPP, event_type, phone, NotificationStatus.SENT)
        except Exception as exc:
            logger.exception("WhatsApp notification failed for %s", application.application_number)
            cls._create_log(
                application,
                NotificationChannel.WHATSAPP,
                event_type,
                phone,
                NotificationStatus.FAILED,
                error_message=str(exc),
            )
