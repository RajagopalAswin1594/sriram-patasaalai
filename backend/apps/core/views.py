from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        db_ok = True
        try:
            connection.ensure_connection()
        except Exception:
            db_ok = False
        status_code = 200 if db_ok else 503
        return Response(
            {
                "success": db_ok,
                "data": {
                    "status": "healthy" if db_ok else "unhealthy",
                    "database": "up" if db_ok else "down",
                    "version": "v1",
                },
            },
            status=status_code,
        )
