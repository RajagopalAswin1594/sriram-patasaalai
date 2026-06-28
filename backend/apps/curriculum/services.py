from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ConflictError, DomainError
from apps.curriculum.models import CourseModule, Lesson, LessonResource, SyllabusStatus, SyllabusVersion


class SyllabusService:
    @classmethod
    @transaction.atomic
    def create_version(cls, course, version_label: str, notes: str = "", fork_from=None):
        last = SyllabusVersion.objects.filter(course=course, is_deleted=False).order_by("-version_number").first()
        version_number = (last.version_number + 1) if last else 1
        syllabus = SyllabusVersion.objects.create(
            course=course,
            version_label=version_label,
            version_number=version_number,
            notes=notes,
        )
        if fork_from:
            cls._fork_structure(fork_from, syllabus)
        return syllabus

    @classmethod
    def _fork_structure(cls, source: SyllabusVersion, target: SyllabusVersion):
        for module in source.modules.filter(is_deleted=False).prefetch_related("lessons", "lessons__resources"):
            new_module = CourseModule.objects.create(
                syllabus=target,
                title=module.title,
                title_sa=module.title_sa,
                title_ta=module.title_ta,
                description=module.description,
                sort_order=module.sort_order,
            )
            for lesson in module.lessons.filter(is_deleted=False):
                new_lesson = Lesson.objects.create(
                    module=new_module,
                    title=lesson.title,
                    title_sa=lesson.title_sa,
                    title_ta=lesson.title_ta,
                    content_text=lesson.content_text,
                    sort_order=lesson.sort_order,
                    estimated_minutes=lesson.estimated_minutes,
                )
                for resource in lesson.resources.filter(is_deleted=False):
                    LessonResource.objects.create(
                        lesson=new_lesson,
                        resource_type=resource.resource_type,
                        title=resource.title,
                        file_name=resource.file_name,
                        content_type=resource.content_type,
                        file_size=resource.file_size,
                        s3_bucket=resource.s3_bucket,
                        s3_key=resource.s3_key,
                        duration_seconds=resource.duration_seconds,
                        text_body=resource.text_body,
                    )

    @classmethod
    @transaction.atomic
    def publish(cls, syllabus: SyllabusVersion):
        if syllabus.status != SyllabusStatus.DRAFT:
            raise ConflictError("Only draft syllabi can be published.")
        SyllabusVersion.objects.filter(
            course=syllabus.course,
            status=SyllabusStatus.PUBLISHED,
            is_deleted=False,
        ).update(status=SyllabusStatus.ARCHIVED)
        syllabus.status = SyllabusStatus.PUBLISHED
        syllabus.published_at = timezone.now()
        syllabus.save(update_fields=["status", "published_at", "updated_at"])
        return syllabus

    @classmethod
    def get_published_syllabus(cls, course):
        return SyllabusVersion.objects.filter(
            course=course,
            status=SyllabusStatus.PUBLISHED,
            is_deleted=False,
        ).first()
