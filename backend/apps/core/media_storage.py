import logging
import uuid
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

MEDIA_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "text/html",
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "video/webm",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/m4a",
    "audio/webm",
    "audio/ogg",
}

PRACTICE_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/m4a",
    "audio/webm",
    "audio/ogg",
}


class MediaStorageService:
    @staticmethod
    def is_s3_enabled():
        return bool(getattr(settings, "AWS_STORAGE_BUCKET_NAME", None))

    @classmethod
    def validate_file(cls, file_name: str, content_type: str, file_size: int, allowed_types=None, max_mb=None):
        allowed = allowed_types or MEDIA_CONTENT_TYPES
        max_bytes = (max_mb or getattr(settings, "MEDIA_MAX_FILE_SIZE_MB", 50)) * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(f"File exceeds maximum size of {max_mb or settings.MEDIA_MAX_FILE_SIZE_MB} MB.")
        if content_type not in allowed:
            raise ValueError("File type not allowed.")
        ext = Path(file_name).suffix.lower()
        if ext not in {
            ".pdf", ".txt", ".html", ".jpg", ".jpeg", ".png", ".webp",
            ".mp4", ".webm", ".mp3", ".wav", ".m4a", ".ogg",
        }:
            raise ValueError("Invalid file extension.")

    @staticmethod
    def build_key(prefix: str, entity_id, file_name: str) -> str:
        ext = Path(file_name).suffix.lower() or ".bin"
        return f"{prefix}/{entity_id}/{uuid.uuid4()}{ext}"

    @classmethod
    def generate_presigned_upload(cls, prefix: str, entity_id, file_name: str, content_type: str, file_size: int, allowed_types=None, max_mb=None):
        cls.validate_file(file_name, content_type, file_size, allowed_types=allowed_types, max_mb=max_mb)
        s3_key = cls.build_key(prefix, entity_id, file_name)

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
                    ["content-length-range", 1, (max_mb or getattr(settings, "MEDIA_MAX_FILE_SIZE_MB", 50)) * 1024 * 1024],
                ],
                ExpiresIn=settings.MEDIA_PRESIGNED_URL_EXPIRY_SECONDS,
            )
            return {
                "upload_type": "s3_presigned_post",
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "key": s3_key,
                "upload_url": presigned["url"],
                "fields": presigned["fields"],
            }

        return {
            "upload_type": "local",
            "bucket": "local",
            "key": s3_key,
            "upload_url": f"{settings.PUBLIC_API_BASE_URL}/api/v1/media/uploads/local/",
            "fields": {"key": s3_key, "Content-Type": content_type},
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
    def get_stream_url(cls, s3_bucket: str, s3_key: str, content_type: str, file_name: str, inline=True) -> str | None:
        if s3_bucket == "local":
            return f"{settings.PUBLIC_API_BASE_URL}/api/v1/media/stream/local/?key={s3_key}"
        if not cls.is_s3_enabled():
            return None
        import boto3

        disposition = "inline" if inline else "attachment"
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
                "ResponseContentDisposition": f'{disposition}; filename="{file_name}"',
                "ResponseContentType": content_type or "application/octet-stream",
            },
            ExpiresIn=settings.MEDIA_PRESIGNED_URL_EXPIRY_SECONDS,
        )

    @classmethod
    def open_local_stream(cls, s3_key: str):
        path = Path(settings.MEDIA_ROOT) / s3_key
        if not path.exists():
            raise FileNotFoundError("Media file not found.")
        return open(path, "rb")
