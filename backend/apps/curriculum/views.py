from django.db import transaction
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.academics.models import VedicCourse
from apps.core.context import set_audit_context
from apps.core.media_storage import MediaStorageService
from apps.curriculum.models import CourseModule, Lesson, LessonResource, ResourceType, SyllabusVersion
from apps.curriculum.serializers import (
    CourseModuleSerializer,
    LessonSerializer,
    LessonWriteSerializer,
    ModuleWriteSerializer,
    ResourceConfirmSerializer,
    ResourcePresignSerializer,
    SyllabusCreateSerializer,
    SyllabusVersionSerializer,
    TextResourceSerializer,
)
from apps.curriculum.services import SyllabusService
from apps.rbac.permissions import require_permission


class SyllabusListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("curriculum.view")]
    serializer_class = SyllabusVersionSerializer

    def get_queryset(self):
        qs = SyllabusVersion.objects.select_related("course").prefetch_related(
            "modules__lessons__resources"
        ).filter(is_deleted=False)
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs.order_by("-version_number")

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("curriculum.add")()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        serializer = SyllabusCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        course = generics.get_object_or_404(VedicCourse, id=serializer.validated_data["course_id"])
        fork_from = None
        if fork_id := serializer.validated_data.get("fork_from_id"):
            fork_from = generics.get_object_or_404(SyllabusVersion, id=fork_id, course=course)
        syllabus = SyllabusService.create_version(
            course,
            serializer.validated_data["version_label"],
            serializer.validated_data.get("notes", ""),
            fork_from=fork_from,
        )
        return Response({"success": True, "data": SyllabusVersionSerializer(syllabus).data}, status=201)


class SyllabusDetailView(generics.RetrieveAPIView):
    permission_classes = [require_permission("curriculum.view")]
    serializer_class = SyllabusVersionSerializer
    lookup_field = "id"
    queryset = SyllabusVersion.objects.select_related("course").prefetch_related("modules__lessons__resources")


class SyllabusPublishView(APIView):
    permission_classes = [require_permission("curriculum.change")]

    def post(self, request, id):
        syllabus = generics.get_object_or_404(SyllabusVersion, id=id, is_deleted=False)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        syllabus = SyllabusService.publish(syllabus)
        return Response({"success": True, "data": SyllabusVersionSerializer(syllabus).data})


class ModuleListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("curriculum.view")]
    serializer_class = CourseModuleSerializer

    def get_queryset(self):
        qs = CourseModule.objects.prefetch_related("lessons__resources").filter(is_deleted=False)
        syllabus_id = self.request.query_params.get("syllabus_id")
        if syllabus_id:
            qs = qs.filter(syllabus_id=syllabus_id)
        return qs

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("curriculum.add")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = ModuleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        module = CourseModule.objects.create(**serializer.validated_data)
        return Response({"success": True, "data": CourseModuleSerializer(module).data}, status=201)


class LessonListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("curriculum.view")]
    serializer_class = LessonSerializer

    def get_queryset(self):
        qs = Lesson.objects.prefetch_related("resources").filter(is_deleted=False)
        module_id = self.request.query_params.get("module_id")
        if module_id:
            qs = qs.filter(module_id=module_id)
        return qs

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("curriculum.add")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = LessonWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        lesson = Lesson.objects.create(**serializer.validated_data)
        return Response({"success": True, "data": LessonSerializer(lesson).data}, status=201)


class ResourcePresignView(APIView):
    permission_classes = [require_permission("curriculum.add")]

    def post(self, request):
        serializer = ResourcePresignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lesson = generics.get_object_or_404(Lesson, id=data["lesson_id"])
        presigned = MediaStorageService.generate_presigned_upload(
            "curriculum",
            lesson.id,
            data["file_name"],
            data["content_type"],
            data["file_size"],
        )
        resource = LessonResource.objects.create(
            lesson=lesson,
            resource_type=data["resource_type"],
            title=data["title"],
            file_name=data["file_name"],
            content_type=data["content_type"],
            file_size=data["file_size"],
            s3_bucket=presigned["bucket"],
            s3_key=presigned["key"],
        )
        return Response({"success": True, "data": {"resource_id": str(resource.id), "upload": presigned}})


class ResourceConfirmView(APIView):
    permission_classes = [require_permission("curriculum.add")]

    def post(self, request):
        serializer = ResourceConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resource = generics.get_object_or_404(LessonResource, id=serializer.validated_data["resource_id"])
        if duration := serializer.validated_data.get("duration_seconds"):
            resource.duration_seconds = duration
            resource.save(update_fields=["duration_seconds", "updated_at"])
        return Response({"success": True, "data": {"resource_id": str(resource.id)}})


class TextResourceCreateView(APIView):
    permission_classes = [require_permission("curriculum.add")]

    def post(self, request):
        serializer = TextResourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lesson = generics.get_object_or_404(Lesson, id=data["lesson_id"])
        resource = LessonResource.objects.create(
            lesson=lesson,
            resource_type=ResourceType.TEXT,
            title=data["title"],
            text_body=data["text_body"],
        )
        from apps.curriculum.serializers import LessonResourceSerializer

        return Response({"success": True, "data": LessonResourceSerializer(resource).data}, status=201)


class ResourceStreamView(APIView):
    permission_classes = [require_permission("curriculum.view")]

    def get(self, request, id):
        resource = generics.get_object_or_404(LessonResource, id=id, is_deleted=False)
        if resource.text_body:
            return Response({"success": True, "data": {"type": "text", "body": resource.text_body}})
        if not resource.s3_key:
            return Response({"success": False, "error": {"message": "No media attached."}}, status=404)
        url = MediaStorageService.get_stream_url(
            resource.s3_bucket, resource.s3_key, resource.content_type, resource.file_name or "media"
        )
        return Response({"success": True, "data": {"type": "url", "url": url, "content_type": resource.content_type}})


class ContentSearchView(APIView):
    permission_classes = [require_permission("curriculum.view")]

    def get(self, request):
        from django.db.models import Q

        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            return Response({"success": False, "error": {"message": "Query must be at least 2 characters."}}, status=400)

        lessons = Lesson.objects.filter(
            Q(title__icontains=q) | Q(title_sa__icontains=q) | Q(title_ta__icontains=q) | Q(content_text__icontains=q),
            is_deleted=False,
        ).select_related("module__syllabus__course")[:25]

        resources = LessonResource.objects.filter(
            Q(title__icontains=q) | Q(text_body__icontains=q),
            is_deleted=False,
        ).select_related("lesson")[:25]

        return Response({
            "success": True,
            "data": {
                "lessons": [
                    {
                        "id": str(l.id),
                        "title": l.title,
                        "title_sa": l.title_sa,
                        "module": l.module.title,
                        "course": l.module.syllabus.course.name if l.module.syllabus else "",
                    }
                    for l in lessons
                ],
                "resources": [
                    {
                        "id": str(r.id),
                        "title": r.title,
                        "resource_type": r.resource_type,
                        "lesson_id": str(r.lesson_id),
                        "lesson_title": r.lesson.title,
                    }
                    for r in resources
                ],
            },
        })
