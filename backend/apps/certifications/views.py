from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User, UserType
from apps.academics.models import Batch, VedicCourse
from apps.branches.models import Branch
from apps.certifications.models import Certificate
from apps.certifications.serializers import CertificateIssueSerializer, CertificateSerializer, CertificateVerifySerializer
from apps.certifications.services import CertificateService
from apps.core.context import set_audit_context
from apps.rbac.permissions import require_permission


class CertificateListView(generics.ListAPIView):
    permission_classes = [require_permission("certifications.view")]
    serializer_class = CertificateSerializer
    queryset = Certificate.objects.filter(is_deleted=False).order_by("-issued_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class CertificateIssueView(APIView):
    permission_classes = [require_permission("certifications.issue")]

    def post(self, request):
        serializer = CertificateIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        student = generics.get_object_or_404(User, id=data["student_id"], user_type=UserType.STUDENT)
        course = generics.get_object_or_404(VedicCourse, id=data["course_id"])
        batch = generics.get_object_or_404(Batch, id=data["batch_id"])
        branch = batch.branch
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        cert = CertificateService.issue(student, course, batch, request.user, branch.name)
        return Response({"success": True, "data": CertificateSerializer(cert).data}, status=201)


class CertificateVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, code):
        cert = CertificateService.verify(code)
        if not cert:
            return Response({"success": False, "error": {"message": "Certificate not found or revoked."}}, status=404)
        return Response({"success": True, "data": CertificateVerifySerializer(cert).data})
