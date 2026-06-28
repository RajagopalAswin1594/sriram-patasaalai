import hashlib
import hmac
import logging
import secrets
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import DomainError
from apps.core.media_storage import MediaStorageService
from apps.donations.models import Donation, DonationCategory, DonationReceipt, DonationStatus

logger = logging.getLogger(__name__)


class DonationPaymentService:
    @staticmethod
    def is_razorpay_enabled():
        return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)

    @classmethod
    @transaction.atomic
    def initiate(cls, data: dict) -> tuple[Donation, dict]:
        category = DonationCategory.objects.filter(code=data["category_code"], is_active=True, is_deleted=False).first()
        if not category:
            raise DomainError("Invalid donation category.")

        amount = Decimal(str(data["amount"]))
        if amount < category.min_amount:
            raise DomainError(f"Minimum donation for this category is ₹{category.min_amount}.")

        donation = Donation.objects.create(
            category=category,
            branch_id=data.get("branch_id"),
            sponsored_student_id=data.get("sponsored_student_id"),
            sponsored_acharya_id=data.get("sponsored_acharya_id"),
            donor_name=data["donor_name"],
            donor_email=data.get("donor_email", ""),
            donor_phone=data.get("donor_phone", ""),
            pan_number=data.get("pan_number", ""),
            amount=amount,
            currency="INR",
            status=DonationStatus.PENDING,
            idempotency_key=data.get("idempotency_key") or secrets.token_hex(16),
        )

        if cls.is_razorpay_enabled():
            import razorpay

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount_paise = int(amount * 100)
            order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": donation.donation_number,
                    "notes": {"donation_id": str(donation.id)},
                }
            )
            donation.gateway_order_id = order["id"]
            donation.status = DonationStatus.INITIATED
            donation.save(update_fields=["gateway_order_id", "status", "updated_at"])
            return donation, {
                "gateway": "RAZORPAY",
                "order_id": order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID,
                "donation_id": str(donation.id),
                "donation_number": donation.donation_number,
            }

        donation.gateway_order_id = f"demo_{donation.donation_number}"
        donation.status = DonationStatus.INITIATED
        donation.save(update_fields=["gateway_order_id", "status", "updated_at"])
        return donation, {
            "gateway": "DEMO",
            "order_id": donation.gateway_order_id,
            "amount": int(amount * 100),
            "currency": "INR",
            "demo_mode": True,
            "donation_id": str(donation.id),
            "donation_number": donation.donation_number,
        }

    @classmethod
    def _verify_signature(cls, order_id: str, payment_id: str, signature: str) -> bool:
        message = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @classmethod
    @transaction.atomic
    def complete_donation(cls, donation: Donation, payment_id: str, signature: str = "", webhook_event_id: str = ""):
        if donation.status == DonationStatus.COMPLETED:
            return donation

        if donation.gateway_order_id and payment_id and signature and cls.is_razorpay_enabled():
            if not cls._verify_signature(donation.gateway_order_id, payment_id, signature):
                raise DomainError("Invalid payment signature.")

        donation.gateway_payment_id = payment_id
        donation.gateway_signature = signature
        donation.webhook_event_id = webhook_event_id or donation.webhook_event_id
        donation.status = DonationStatus.COMPLETED
        donation.paid_at = timezone.now()
        donation.save(
            update_fields=[
                "gateway_payment_id",
                "gateway_signature",
                "webhook_event_id",
                "status",
                "paid_at",
                "updated_at",
            ]
        )

        receipt = DonationReceiptService.generate(donation)
        DonationReceiptService.send_receipt_notification(donation, receipt)
        return donation

    @classmethod
    @transaction.atomic
    def confirm_demo(cls, donation_id):
        donation = Donation.objects.select_for_update().filter(id=donation_id, is_deleted=False).first()
        if not donation:
            raise DomainError("Donation not found.")
        return cls.complete_donation(donation, payment_id=f"demo_{donation.donation_number}")

    @classmethod
    @transaction.atomic
    def handle_webhook(cls, event: dict):
        event_id = event.get("id", "")
        if event_id and Donation.objects.filter(webhook_event_id=event_id).exists():
            return {"status": "already_processed"}

        payload = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payload.get("order_id")
        payment_id = payload.get("id")
        if not order_id or not payment_id:
            return {"status": "ignored"}

        donation = Donation.objects.select_for_update().filter(gateway_order_id=order_id).first()
        if not donation:
            logger.warning("Webhook for unknown order %s", order_id)
            return {"status": "not_found"}

        cls.complete_donation(donation, payment_id=payment_id, webhook_event_id=event_id)
        return {"status": "completed", "donation_number": donation.donation_number}


class DonationReceiptService:
    @classmethod
    @transaction.atomic
    def generate(cls, donation: Donation) -> DonationReceipt:
        existing = DonationReceipt.objects.filter(donation=donation).first()
        if existing:
            return existing

        receipt_number = f"RCP-{donation.donation_number}"
        pdf_bytes = cls._build_pdf(donation, receipt_number)
        s3_key = MediaStorageService.build_key("donations", donation.id, f"{receipt_number}.pdf")

        if MediaStorageService.is_s3_enabled():
            import boto3

            client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            client.put_object(Bucket=bucket, Key=s3_key, Body=pdf_bytes, ContentType="application/pdf")
            pdf_bucket = bucket
        else:
            from apps.certifications.services import _BytesFile

            MediaStorageService.save_local_file(s3_key, _BytesFile(pdf_bytes, f"{receipt_number}.pdf"))
            pdf_bucket = "local"

        return DonationReceipt.objects.create(
            donation=donation,
            receipt_number=receipt_number,
            registration_12a=getattr(settings, "DONATION_12A_REGISTRATION", ""),
            registration_80g=getattr(settings, "DONATION_80G_REGISTRATION", ""),
            pdf_s3_bucket=pdf_bucket,
            pdf_s3_key=s3_key,
        )

    @classmethod
    def _build_pdf(cls, donation: Donation, receipt_number: str) -> bytes:
        import io

        org_name = getattr(settings, "ORGANIZATION_LEGAL_NAME", "Digital Veda Gurukulam Trust")
        reg_12a = getattr(settings, "DONATION_12A_REGISTRATION", "12A/XXXX/XXXX")
        reg_80g = getattr(settings, "DONATION_80G_REGISTRATION", "80G/XXXX/XXXX")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width / 2, height - 60, "Donation Tax Receipt")
            c.setFont("Helvetica", 11)
            c.drawCentredString(width / 2, height - 85, org_name)
            c.drawCentredString(width / 2, height - 105, f"12A Registration: {reg_12a}")
            c.drawCentredString(width / 2, height - 120, f"80G Registration: {reg_80g}")
            c.line(50, height - 135, width - 50, height - 135)
            y = height - 165
            lines = [
                f"Receipt No: {receipt_number}",
                f"Donation No: {donation.donation_number}",
                f"Date: {donation.paid_at.strftime('%d %B %Y') if donation.paid_at else ''}",
                f"Donor: {donation.donor_name}",
                f"PAN: {donation.pan_number or '—'}",
                f"Category: {donation.category.name}",
                f"Amount: ₹{donation.amount}",
                f"Payment ID: {donation.gateway_payment_id}",
            ]
            for line in lines:
                c.drawString(60, y, line)
                y -= 22
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(60, 80, "This receipt is valid for income tax deduction under Section 80G of the IT Act, 1961.")
            c.showPage()
            c.save()
            return buffer.getvalue()
        except ImportError:
            return f"{receipt_number}\n{donation.donor_name}\n{donation.amount}".encode("utf-8")

    @classmethod
    def send_receipt_notification(cls, donation: Donation, receipt: DonationReceipt):
        if not donation.donor_email:
            return
        from apps.notifications.services import NotificationDispatcher

        NotificationDispatcher.send(
            template_code="DONATION_RECEIPT",
            recipient_email=donation.donor_email,
            recipient_phone=donation.donor_phone,
            context={
                "donor_name": donation.donor_name,
                "amount": str(donation.amount),
                "receipt_number": receipt.receipt_number,
                "category": donation.category.name,
            },
            idempotency_key=f"donation-receipt-{donation.id}",
        )
