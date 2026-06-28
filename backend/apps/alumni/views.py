from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alumni.models import AlumniProfile
from apps.alumni.serializers import AlumniProfileSerializer, AlumniRegisterSerializer
from apps.alumni.services import AlumniRegistrationService
from apps.core.exceptions import DomainError
from apps.rbac.permissions import require_permission


class AlumniRegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AlumniRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, profile = AlumniRegistrationService.register(serializer.validated_data)
        except DomainError as exc:
            return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        return Response(
            {"success": True, "data": AlumniProfileSerializer(profile).data},
            status=201,
        )


class AlumniDirectoryListView(generics.ListAPIView):
    permission_classes = [require_permission("alumni.view")]
    serializer_class = AlumniProfileSerializer

    def get_queryset(self):
        qs = AlumniProfile.objects.filter(is_deleted=False, is_directory_visible=True).select_related(
            "user", "user__profile", "branch"
        )
        year = self.request.query_params.get("graduation_year")
        if year:
            qs = qs.filter(graduation_year=year)
        city = self.request.query_params.get("city")
        if city:
            qs = qs.filter(current_city__icontains=city)
        return qs.order_by("-graduation_year")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})


class AlumniMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = AlumniProfile.objects.filter(user=request.user, is_deleted=False).first()
        if not profile:
            return Response({"success": False, "error": {"message": "Alumni profile not found."}}, status=404)
        return Response({"success": True, "data": AlumniProfileSerializer(profile).data})

    def patch(self, request):
        profile = AlumniProfile.objects.filter(user=request.user, is_deleted=False).first()
        if not profile:
            return Response({"success": False, "error": {"message": "Alumni profile not found."}}, status=404)
        serializer = AlumniProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})
