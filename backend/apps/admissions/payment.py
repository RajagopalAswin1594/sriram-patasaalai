import hashlib
import hmac
import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.admissions.models import (
    AdmissionApplication,
    ApplicationPayment,
    ApplicationStatus,
    PaymentGateway,
    PaymentStatus,
)
from apps.core.exceptions import DomainError

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def is_razorpay_enabled():
        return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)

    @classmethod
    @transaction.atomic
    def initiate_payment(cls, application: AdmissionApplication):
        payment, _ = ApplicationPayment.objects.get_or_create(
            application=application,
            defaults={
                "amount": application.application_fee_amount,
                "currency": "INR",
            },
        )
        if payment.status == PaymentStatus.COMPLETED:
            raise DomainError("Payment already completed.")

        if cls.is_razorpay_enabled():
            import razorpay

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount_paise = int(application.application_fee_amount * 100)
            order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": application.application_number,
                    "notes": {"application_id": str(application.id)},
                }
            )
            payment.gateway = PaymentGateway.RAZORPAY
            payment.gateway_order_id = order["id"]
            payment.status = PaymentStatus.INITIATED
            payment.save()
            return {
                "gateway": PaymentGateway.RAZORPAY,
                "order_id": order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID,
                "application_number": application.application_number,
            }

        payment.gateway = PaymentGateway.DEMO
        payment.gateway_order_id = f"demo_{application.application_number}"
        payment.status = PaymentStatus.INITIATED
        payment.save()
        return {
            "gateway": PaymentGateway.DEMO,
            "order_id": payment.gateway_order_id,
            "amount": int(application.application_fee_amount * 100),
            "currency": "INR",
            "demo_mode": True,
            "application_number": application.application_number,
        }

    @classmethod
    @transaction.atomic
    def confirm_demo_payment(cls, application: AdmissionApplication):
        payment = application.payment
        if payment.gateway != PaymentGateway.DEMO:
            raise DomainError("Demo payment not available.")
        payment.status = PaymentStatus.COMPLETED
        payment.gateway_payment_id = f"demo_pay_{application.application_number}"
        payment.paid_at = timezone.now()
        payment.save()
        from apps.admissions.review import ReviewWorkflowService

        ReviewWorkflowService.mark_pending_review(application)
        return payment

    @classmethod
    @transaction.atomic
    def verify_razorpay_payment(cls, application: AdmissionApplication, order_id: str, payment_id: str, signature: str):
        if not cls.is_razorpay_enabled():
            raise DomainError("Razorpay is not configured.")

        message = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise DomainError("Invalid payment signature.")

        payment = application.payment
        payment.gateway_order_id = order_id
        payment.gateway_payment_id = payment_id
        payment.gateway_signature = signature
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = timezone.now()
        payment.save()
        from apps.admissions.review import ReviewWorkflowService

        ReviewWorkflowService.mark_pending_review(application)
        return payment
