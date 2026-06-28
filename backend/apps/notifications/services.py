import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.notifications.models import NotificationChannel, NotificationDeliveryStatus, NotificationLog, NotificationTemplate

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """Unified notification center with template rendering and idempotency."""

    @classmethod
    def send(
        cls,
        template_code: str,
        recipient_email: str = "",
        recipient_phone: str = "",
        context: dict | None = None,
        idempotency_key: str = "",
        user=None,
        branch=None,
        channels: list[str] | None = None,
    ):
        context = context or {}
        selected_channels = channels or ["EMAIL", "SMS", "WHATSAPP"]
        results = []

        templates = NotificationTemplate.objects.filter(code=template_code, is_active=True, is_deleted=False)
        if not templates.exists():
            templates = [cls._default_template(template_code)]

        for template in templates:
            if template.channel not in selected_channels:
                continue
            recipient = recipient_email if template.channel == NotificationChannel.EMAIL else recipient_phone
            if not recipient:
                continue
            if idempotency_key and NotificationLog.objects.filter(
                idempotency_key=idempotency_key, channel=template.channel
            ).exists():
                results.append({"channel": template.channel, "status": "skipped_duplicate"})
                continue

            subject = cls._render(template.subject_template, context) if template.subject_template else ""
            body = cls._render(template.body_template, context)
            status, error = cls._deliver(template.channel, recipient, subject, body)

            NotificationLog.objects.create(
                template=template if hasattr(template, "id") else None,
                template_code=template_code,
                channel=template.channel,
                recipient=recipient,
                subject=subject,
                body=body,
                status=status,
                error_message=error,
                idempotency_key=idempotency_key,
                user=user,
                branch=branch,
            )
            results.append({"channel": template.channel, "status": status})
        return results

    @staticmethod
    def _render(template_str: str, context: dict) -> str:
        if not template_str:
            return ""
        rendered = template_str
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered

    @classmethod
    def _deliver(cls, channel: str, recipient: str, subject: str, body: str):
        try:
            if channel == NotificationChannel.EMAIL:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                return NotificationDeliveryStatus.SENT, ""
            if channel == NotificationChannel.SMS:
                if not getattr(settings, "SMS_ENABLED", False):
                    logger.info("[SMS stub] To=%s %s", recipient, body[:60])
                    return NotificationDeliveryStatus.SENT, ""
                import requests

                response = requests.post(
                    settings.SMS_API_URL,
                    headers={"Authorization": f"Bearer {settings.SMS_API_TOKEN}"},
                    json={"to": recipient, "message": body},
                    timeout=15,
                )
                response.raise_for_status()
                return NotificationDeliveryStatus.SENT, ""
            if channel == NotificationChannel.WHATSAPP:
                if not getattr(settings, "WHATSAPP_ENABLED", False):
                    logger.info("[WhatsApp stub] To=%s %s", recipient, body[:60])
                    return NotificationDeliveryStatus.SENT, ""
                import requests

                response = requests.post(
                    settings.WHATSAPP_API_URL,
                    headers={"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}"},
                    json={"to": recipient, "message": body},
                    timeout=15,
                )
                response.raise_for_status()
                return NotificationDeliveryStatus.SENT, ""
        except Exception as exc:
            logger.exception("Notification delivery failed")
            return NotificationDeliveryStatus.FAILED, str(exc)
        return NotificationDeliveryStatus.SKIPPED, "Unknown channel"

    @staticmethod
    def _default_template(code: str):
        class _T:
            channel = NotificationChannel.EMAIL
            subject_template = "{{ subject }}"
            body_template = "{{ body }}"

        if code == "DONATION_RECEIPT":
            _T.subject_template = "Donation Receipt – {{ receipt_number }}"
            _T.body_template = (
                "Dear {{ donor_name }},\n\nThank you for your donation of ₹{{ amount }} "
                "towards {{ category }}.\nReceipt: {{ receipt_number }}\n\n– Gurukulam"
            )
        return _T()
