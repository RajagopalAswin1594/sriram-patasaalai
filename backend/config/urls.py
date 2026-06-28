from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.media_views import LocalMediaStreamView, LocalMediaUploadView
from apps.core.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.rbac.urls")),
    path("api/v1/", include("apps.branches.urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.admissions.urls")),
    path("api/v1/", include("apps.academics.urls")),
    path("api/v1/", include("apps.students.urls")),
    path("api/v1/", include("apps.scheduling.urls")),
    path("api/v1/", include("apps.curriculum.urls")),
    path("api/v1/", include("apps.learning.urls")),
    path("api/v1/", include("apps.certifications.urls")),
    path("api/v1/", include("apps.donations.urls")),
    path("api/v1/", include("apps.hostel.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.community.urls")),
    path("api/v1/", include("apps.chant_evaluator.urls")),
    path("api/v1/", include("apps.alumni.urls")),
    path("api/v1/", include("apps.feedback.urls")),
    path("api/v1/", include("apps.gurukulam_feedback.urls")),
    path("api/v1/media/uploads/local/", LocalMediaUploadView.as_view()),
    path("api/v1/media/stream/local/", LocalMediaStreamView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
