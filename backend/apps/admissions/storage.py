import logging
import mimetypes
import os
import uuid
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


class StorageService:
    @staticmethod
    def is_s3_enabled():
        return bool(getattr(settings, "AWS_STORAGE_BUCKET_NAME", None))

    @staticmethod
    def validate_file(file_name: str, content_type: str, file_size: int):
        max_bytes = settings.ADMISSION_MAX_DOCUMENT_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(f"File exceeds maximum size of {settings.ADMISSION_MAX_DOCUMENT_SIZE_MB} MB.")
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("File type not allowed. Use PDF, JPG, or PNG.")
        ext = Path(file_name).suffix.lower()
        if ext not in {".pdf", ".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError("Invalid file extension.")

    @staticmethod
    def build_s3_key(application_id, document_type: str, file_name: str) -> str:
        ext = Path(file_name).suffix.lower() or ".bin"
        return f"admissions/{application_id}/{document_type.lower()}/{uuid.uuid4()}{ext}"

    @classmethod
    def generate_presigned_upload(cls, application_id, document_type: str, file_name: str, content_type: str, file_size: int):
        cls.validate_file(file_name, content_type, file_size)
        s3_key = cls.build_s3_key(application_id, document_type, file_name)

        if cls.is_s3_enabled():
            import boto3
            from botocore.config import Config

            client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                config=Config(signature_version="s3v4"),
            )
            presigned = client.generate_presigned_post(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=s3_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, settings.ADMISSION_MAX_DOCUMENT_SIZE_MB * 1024 * 1024],
                ],
                ExpiresIn=settings.ADMISSION_PRESIGNED_URL_EXPIRY_SECONDS,
            )
            return {
                "upload_type": "s3_presigned_post",
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "key": s3_key,
                "upload_url": presigned["url"],
                "fields": presigned["fields"],
            }

        local_upload_url = f"{settings.PUBLIC_API_BASE_URL}/api/v1/admissions/uploads/local/"
        return {
            "upload_type": "local",
            "bucket": "local",
            "key": s3_key,
            "upload_url": local_upload_url,
            "fields": {
                "key": s3_key,
                "Content-Type": content_type,
            },
        }

    @classmethod
    def save_local_file(cls, s3_key: str, uploaded_file) -> str:
        media_root = Path(settings.MEDIA_ROOT)
        target = media_root / s3_key
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)
        return str(target)

    @classmethod
    def get_inline_view_url(cls, s3_bucket: str, s3_key: str, content_type: str, file_name: str) -> str | None:
        if s3_bucket == "local":
            return None
        if not cls.is_s3_enabled():
            return None
        import boto3

        client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": s3_bucket,
                "Key": s3_key,
                "ResponseContentDisposition": f'inline; filename="{file_name}"',
                "ResponseContentType": content_type or "application/octet-stream",
            },
            ExpiresIn=settings.ADMISSION_PRESIGNED_URL_EXPIRY_SECONDS,
        )

    @classmethod
    def open_document_stream(cls, document):
        from apps.admissions.models import DocumentUploadStatus

        if document.upload_status not in (
            DocumentUploadStatus.UPLOADED,
            DocumentUploadStatus.VERIFIED,
            DocumentUploadStatus.REJECTED,
            DocumentUploadStatus.RESUBMIT_REQUESTED,
        ):
            raise FileNotFoundError("Document has not been uploaded.")
        if not document.s3_key:
            raise FileNotFoundError("Document storage key is missing.")

        if document.s3_bucket == "local":
            path = Path(settings.MEDIA_ROOT) / document.s3_key
            if not path.exists():
                raise FileNotFoundError("Document file not found on server.")
            return open(path, "rb"), document.content_type or "application/octet-stream", document.file_name

        import boto3

        client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        obj = client.get_object(Bucket=document.s3_bucket, Key=document.s3_key)
        content_type = document.content_type or obj.get("ContentType") or "application/octet-stream"
        return obj["Body"], content_type, document.file_name
