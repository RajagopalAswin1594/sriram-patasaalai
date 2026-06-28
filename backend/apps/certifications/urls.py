from django.urls import path

from apps.certifications.views import CertificateIssueView, CertificateListView, CertificateVerifyView

urlpatterns = [
    path("certifications/", CertificateListView.as_view(), name="certificate-list"),
    path("certifications/issue/", CertificateIssueView.as_view(), name="certificate-issue"),
    path("certifications/verify/<str:code>/", CertificateVerifyView.as_view(), name="certificate-verify"),
]
