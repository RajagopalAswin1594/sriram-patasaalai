import io
import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.certifications.models import Certificate, CertificateStatus
from apps.core.media_storage import MediaStorageService


class CertificateService:
    @classmethod
    def _generate_number(cls):
        year = timezone.now().year
        return f"CERT-{year}-{secrets.token_hex(4).upper()}"

    @classmethod
    def _generate_verification_code(cls):
        return secrets.token_urlsafe(24)

    @classmethod
    @transaction.atomic
    def issue(cls, student, course, batch, issued_by, branch_name: str):
        profile = getattr(student, "profile", None)
        student_name = profile.display_name if profile else student.email
        certificate_number = cls._generate_number()
        verification_code = cls._generate_verification_code()

        pdf_bytes = cls._build_pdf(
            certificate_number=certificate_number,
            verification_code=verification_code,
            student_name=student_name,
            course_name=course.name,
            branch_name=branch_name,
            issued_at=timezone.now(),
        )
        s3_key = MediaStorageService.build_key("certificates", student.id, f"{certificate_number}.pdf")
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
            MediaStorageService.save_local_file(s3_key, _BytesFile(pdf_bytes, "certificate.pdf"))
            pdf_bucket = "local"

        return Certificate.objects.create(
            student=student,
            course=course,
            batch=batch,
            certificate_number=certificate_number,
            verification_code=verification_code,
            student_name=student_name,
            course_name=course.name,
            branch_name=branch_name,
            issued_at=timezone.now(),
            pdf_s3_bucket=pdf_bucket,
            pdf_s3_key=s3_key,
            issued_by=issued_by,
        )

    @classmethod
    def _build_pdf(cls, certificate_number, verification_code, student_name, course_name, branch_name, issued_at):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            c.setFont("Helvetica-Bold", 22)
            c.drawCentredString(width / 2, height - 80, "Digital Veda Gurukulam")
            c.setFont("Helvetica", 14)
            c.drawCentredString(width / 2, height - 110, "Certificate of Completion")
            c.setFont("Helvetica", 12)
            c.drawCentredString(width / 2, height - 160, f"This certifies that")
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, height - 190, student_name)
            c.setFont("Helvetica", 12)
            c.drawCentredString(width / 2, height - 220, f"has completed {course_name}")
            c.drawCentredString(width / 2, height - 240, branch_name)
            c.drawCentredString(width / 2, height - 270, f"Issued: {issued_at.strftime('%d %B %Y')}")
            c.setFont("Helvetica", 10)
            c.drawCentredString(width / 2, height - 310, f"Certificate No: {certificate_number}")
            c.drawCentredString(width / 2, height - 330, f"Verify: {verification_code}")
            c.showPage()
            c.save()
            return buffer.getvalue()
        except ImportError:
            return (
                f"Certificate\n{certificate_number}\n{student_name}\n{course_name}\n{verification_code}".encode("utf-8")
            )

    @classmethod
    def verify(cls, code: str):
        cert = Certificate.objects.filter(verification_code=code, is_deleted=False).first()
        if not cert or cert.status != CertificateStatus.ISSUED:
            return None
        return cert


class _BytesFile:
    def __init__(self, data: bytes, name: str):
        self._data = data
        self.name = name

    def chunks(self):
        yield self._data
