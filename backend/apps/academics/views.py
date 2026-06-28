from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.academics.models import AcademicYear, Batch, Shakha, VedicCourse
from apps.academics.serializers import (
    AcademicYearSerializer,
    BatchSerializer,
    ShakhaSerializer,
    VedicCourseSerializer,
)
from apps.core.branch_scope import branch_scoped_queryset
from apps.core.context import set_audit_context
from apps.rbac.permissions import require_permission


class ShakhaListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("academics.view")]
    serializer_class = ShakhaSerializer
    queryset = Shakha.objects.all().order_by("name")

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("academics.add")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class AcademicYearListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("academics.view")]
    serializer_class = AcademicYearSerializer
    queryset = AcademicYear.objects.all()

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("academics.add")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class VedicCourseListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("academics.view")]
    serializer_class = VedicCourseSerializer
    queryset = VedicCourse.objects.select_related("shakha").all()

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("academics.add")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class BatchListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("academics.view")]
    serializer_class = BatchSerializer

    def get_queryset(self):
        qs = Batch.objects.select_related("branch", "academic_year").prefetch_related("courses").filter(is_deleted=False)
        return branch_scoped_queryset(self.request.user, qs)

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("academics.add")()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class BatchDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [require_permission("academics.view")]
    serializer_class = BatchSerializer
    lookup_field = "id"

    def get_queryset(self):
        qs = Batch.objects.select_related("branch", "academic_year").prefetch_related("courses")
        return branch_scoped_queryset(self.request.user, qs)

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [require_permission("academics.change")()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def update(self, request, *args, **kwargs):
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        response = super().update(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})
