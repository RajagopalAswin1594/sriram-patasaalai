from django.db import transaction
from django.utils import timezone

from apps.admissions.models import (
    AdmissionApplication,
    ApplicationDocument,
    ApplicationPayment,
    ApplicationStatus,
    DocumentType,
    DocumentUploadStatus,
    PaymentStatus,
)
from apps.admissions.payment import PaymentService
from apps.admissions.review import ReviewWorkflowService
from apps.admissions.storage import StorageService
from apps.branches.models import Branch, BranchStatus
from apps.core.exceptions import ConflictError, DomainError


REQUIRED_DOCUMENTS = {
    DocumentType.STUDENT_PHOTO,
    DocumentType.BIRTH_CERTIFICATE,
}


class ApplicationService:
    @staticmethod
    def get_public_application(application_id, access_token: str) -> AdmissionApplication:
        try:
            return AdmissionApplication.objects.get(id=application_id, access_token=access_token, is_deleted=False)
        except AdmissionApplication.DoesNotExist:
            raise DomainError("Application not found.")

    @classmethod
    @transaction.atomic
    def create_draft(cls, data: dict) -> AdmissionApplication:
        branch_id = data.pop("branch_id")
        branch = Branch.objects.filter(id=branch_id, status=BranchStatus.ACTIVE, is_deleted=False).first()
        if not branch:
            raise DomainError("Selected branch is not available for applications.")
        from django.conf import settings

        if "application_fee_amount" not in data:
            data["application_fee_amount"] = settings.ADMISSION_APPLICATION_FEE
        consent = data.pop("data_consent", False)
        if not consent:
            raise DomainError("Data processing consent is required.")
        from django.utils import timezone as tz

        data["data_consent_at"] = tz.now()
        data["data_consent_version"] = getattr(settings, "DATA_CONSENT_VERSION", "v1.0")
        return AdmissionApplication.objects.create(branch=branch, **data)

    @classmethod
    @transaction.atomic
    def update_draft(cls, application: AdmissionApplication, data: dict) -> AdmissionApplication:
        if application.status not in (ApplicationStatus.DRAFT, ApplicationStatus.PAYMENT_PENDING):
            raise ConflictError("Application can no longer be edited.")
        for field, value in data.items():
            setattr(application, field, value)
        application.save()
        return application

    @classmethod
    @transaction.atomic
    def submit(cls, application: AdmissionApplication) -> AdmissionApplication:
        if application.status != ApplicationStatus.DRAFT:
            raise ConflictError("Only draft applications can be submitted.")

        uploaded_types = set(
            application.documents.filter(
                upload_status__in=(
                    DocumentUploadStatus.UPLOADED,
                    DocumentUploadStatus.VERIFIED,
                ),
                is_deleted=False,
            ).values_list("document_type", flat=True)
        )
        missing = REQUIRED_DOCUMENTS - uploaded_types
        if missing:
            raise DomainError(f"Missing required documents: {', '.join(sorted(missing))}")

        application.status = ApplicationStatus.PAYMENT_PENDING
        application.submitted_at = timezone.now()
        application.save(update_fields=["status", "submitted_at", "updated_at"])
        ApplicationPayment.objects.get_or_create(
            application=application,
            defaults={"amount": application.application_fee_amount, "currency": "INR"},
        )
        return application

    @classmethod
    @transaction.atomic
    def presign_document(
        cls,
        application: AdmissionApplication,
        document_type: str,
        file_name: str,
        content_type: str,
        file_size: int,
    ):
        existing = ApplicationDocument.objects.filter(
            application=application,
            document_type=document_type,
            is_deleted=False,
        ).first()

        if application.status in (ApplicationStatus.DRAFT, ApplicationStatus.PAYMENT_PENDING):
            pass
        elif (
            application.status in (ApplicationStatus.PENDING, ApplicationStatus.UNDER_REVIEW)
            and existing
            and existing.upload_status == DocumentUploadStatus.RESUBMIT_REQUESTED
        ):
            pass
        else:
            raise ConflictError("Documents cannot be uploaded at this stage.")

        StorageService.validate_file(file_name, content_type, file_size)
        presigned = StorageService.generate_presigned_upload(
            application.id, document_type, file_name, content_type, file_size
        )

        document, _ = ApplicationDocument.objects.update_or_create(
            application=application,
            document_type=document_type,
            defaults={
                "file_name": file_name,
                "file_size": file_size,
                "content_type": content_type,
                "s3_bucket": presigned["bucket"],
                "s3_key": presigned["key"],
                "upload_status": DocumentUploadStatus.PENDING,
                "uploaded_at": None,
                "review_notes": "",
                "reviewed_at": None,
                "reviewed_by": None,
            },
        )
        return document, presigned

    @classmethod
    @transaction.atomic
    def confirm_document_upload(cls, application: AdmissionApplication, document_id) -> ApplicationDocument:
        document = ApplicationDocument.objects.filter(application=application, id=document_id).first()
        if not document:
            raise DomainError("Document not found.")
        document.upload_status = DocumentUploadStatus.UPLOADED
        document.uploaded_at = timezone.now()
        document.save(update_fields=["upload_status", "uploaded_at", "updated_at"])
        return document

    @classmethod
    @transaction.atomic
    def review(cls, application: AdmissionApplication, status: str, actor, rejection_reason: str = "", review_notes: str = ""):
        from apps.admissions.state_machine import assert_review_decision

        assert_review_decision(status)
        if status == ApplicationStatus.APPROVED:
            return ReviewWorkflowService.approve(application, actor, review_notes=review_notes)
        return ReviewWorkflowService.reject(application, actor, rejection_reason=rejection_reason, review_notes=review_notes)
