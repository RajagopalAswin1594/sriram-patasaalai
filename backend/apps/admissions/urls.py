from django.urls import path

from apps.admissions.views import (
    AdminApplicationAssignView,
    AdminApplicationDetailView,
    AdminApplicationHistoryView,
    AdminApplicationListView,
    AdminApplicationReviewView,
    AdminApplicationStatsView,
    AdminDocumentReviewView,
    AdminDocumentViewView,
    DocumentConfirmView,
    DocumentPresignView,
    LocalDocumentUploadView,
    PaymentConfirmView,
    PaymentInitiateView,
    PublicApplicationCreateView,
    PublicApplicationDetailView,
    PublicApplicationSubmitView,
    PublicBranchListView,
)

urlpatterns = [
    path("admissions/branches/", PublicBranchListView.as_view(), name="admission-branches"),
    path("admissions/applications/", PublicApplicationCreateView.as_view(), name="admission-create"),
    path("admissions/applications/<uuid:id>/", PublicApplicationDetailView.as_view(), name="admission-detail"),
    path("admissions/applications/<uuid:id>/submit/", PublicApplicationSubmitView.as_view(), name="admission-submit"),
    path("admissions/applications/<uuid:id>/documents/presign/", DocumentPresignView.as_view(), name="admission-presign"),
    path("admissions/applications/<uuid:id>/documents/confirm/", DocumentConfirmView.as_view(), name="admission-doc-confirm"),
    path("admissions/applications/<uuid:id>/payment/initiate/", PaymentInitiateView.as_view(), name="admission-payment-init"),
    path("admissions/applications/<uuid:id>/payment/confirm/", PaymentConfirmView.as_view(), name="admission-payment-confirm"),
    path("admissions/uploads/local/", LocalDocumentUploadView.as_view(), name="admission-local-upload"),
    path("admissions/admin/applications/", AdminApplicationListView.as_view(), name="admission-admin-list"),
    path("admissions/admin/applications/<uuid:id>/", AdminApplicationDetailView.as_view(), name="admission-admin-detail"),
    path("admissions/admin/applications/<uuid:id>/review/", AdminApplicationReviewView.as_view(), name="admission-review"),
    path("admissions/admin/applications/<uuid:id>/assign/", AdminApplicationAssignView.as_view(), name="admission-assign"),
    path("admissions/admin/applications/<uuid:id>/history/", AdminApplicationHistoryView.as_view(), name="admission-history"),
    path(
        "admissions/admin/applications/<uuid:id>/documents/<uuid:document_id>/view/",
        AdminDocumentViewView.as_view(),
        name="admission-document-view",
    ),
    path(
        "admissions/admin/applications/<uuid:id>/documents/<uuid:document_id>/review/",
        AdminDocumentReviewView.as_view(),
        name="admission-document-review",
    ),
    path("admissions/admin/stats/", AdminApplicationStatsView.as_view(), name="admission-stats"),
]
