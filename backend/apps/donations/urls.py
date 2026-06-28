from django.urls import path

from apps.donations.views import (
    DonationListView,
    DonorMyDonationsView,
    PublicDonationCategoryListView,
    PublicDonationConfirmView,
    PublicDonationInitiateView,
    RazorpayDonationWebhookView,
)

urlpatterns = [
    path("donations/categories/", PublicDonationCategoryListView.as_view()),
    path("donations/initiate/", PublicDonationInitiateView.as_view()),
    path("donations/confirm/", PublicDonationConfirmView.as_view()),
    path("donations/webhooks/razorpay/", RazorpayDonationWebhookView.as_view()),
    path("donations/", DonationListView.as_view()),
    path("donations/my/", DonorMyDonationsView.as_view()),
]
