from django.http import FileResponse, Http404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.media_storage import MediaStorageService


class LocalMediaUploadView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get("file")
        s3_key = request.data.get("key")
        if not uploaded or not s3_key:
            return Response({"success": False, "error": {"message": "file and key required."}}, status=400)
        MediaStorageService.save_local_file(s3_key, uploaded)
        return Response({"success": True})


class LocalMediaStreamView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        s3_key = request.query_params.get("key")
        if not s3_key:
            raise Http404("Key required.")
        try:
            stream = MediaStorageService.open_local_stream(s3_key)
        except FileNotFoundError as exc:
            raise Http404(str(exc)) from exc
        return FileResponse(stream, as_attachment=False)
