from django.db import models

from apps.core.models import AuditableModel


class CertificateStatus(models.TextChoices):
    ISSUED = "ISSUED", "Issued"
    REVOKED = "REVOKED", "Revoked"


class Certificate(AuditableModel):
    student = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="certificates")
    course = models.ForeignKey("academics.VedicCourse", on_delete=models.PROTECT, related_name="certificates")
    batch = models.ForeignKey("academics.Batch", on_delete=models.PROTECT, related_name="certificates")
    certificate_number = models.CharField(max_length=40, unique=True)
    verification_code = models.CharField(max_length=64, unique=True, db_index=True)
    student_name = models.CharField(max_length=200)
    course_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200)
    issued_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=CertificateStatus.choices, default=CertificateStatus.ISSUED)
    pdf_s3_bucket = models.CharField(max_length=100, blank=True)
    pdf_s3_key = models.CharField(max_length=500, blank=True)
    issued_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="certificates_issued",
    )

    class Meta:
        ordering = ["-issued_at"]
