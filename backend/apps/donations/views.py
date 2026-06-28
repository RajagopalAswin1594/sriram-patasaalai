import hashlib
import hmac
import json
import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.branch_scope import branch_scoped_queryset
from apps.core.context import set_audit_context
from apps.core.exceptions import DomainError
from apps.donations.models import Donation, DonationCategory
from apps.donations.payment import DonationPaymentService
from apps.donations.serializers import (
    DonationCategorySerializer,
    DonationConfirmSerializer,
    DonationInitiateSerializer,
    DonationSerializer,
)
from apps.rbac.permissions import require_permission

logger = logging.getLogger(__name__)


class PublicDonationCategoryListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        categories = DonationCategory.objects.filter(is_active=True, is_deleted=False).order_by("name")
        return Response({"success": True, "data": DonationCategorySerializer(categories, many=True).data})


class PublicDonationInitiateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = DonationInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            donation, payment = DonationPaymentService.initiate(serializer.validated_data)
        except DomainError as exc:
            return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        return Response(
            {"success": True, "data": {"donation": DonationSerializer(donation).data, "payment": payment}},
            status=status.HTTP_201_CREATED,
        )


class PublicDonationConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = DonationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        donation = Donation.objects.filter(id=data["donation_id"], is_deleted=False).first()
        if not donation:
            return Response({"success": False, "error": {"message": "Donation not found."}}, status=404)

        if payment := data.get("razorpay_payment_id"):
            try:
                donation = DonationPaymentService.complete_donation(
                    donation,
                    payment_id=payment,
                    signature=data.get("razorpay_signature", ""),
                )
            except DomainError as exc:
                return Response({"success": False, "error": {"message": str(exc)}}, status=400)
        else:
            donation = DonationPaymentService.confirm_demo(donation.id)

        return Response({"success": True, "data": DonationSerializer(donation).data})


class RazorpayDonationWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body
        signature = request.headers.get("X-Razorpay-Signature", "")
        webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "")
        if webhook_secret and signature:
            expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return Response({"success": False, "error": {"message": "Invalid signature."}}, status=400)

        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            return Response({"success": False, "error": {"message": "Invalid payload."}}, status=400)

        try:
            result = DonationPaymentService.handle_webhook(event)
        except Exception:
            logger.exception("Donation webhook processing failed")
            return Response({"success": False, "error": {"message": "Processing failed."}}, status=500)

        return Response({"success": True, "data": result})


class DonationListView(generics.ListAPIView):
    permission_classes = [require_permission("donations.view")]
    serializer_class = DonationSerializer

    def get_queryset(self):
        qs = Donation.objects.filter(is_deleted=False).select_related("category").order_by("-created_at")
        return branch_scoped_queryset(self.request.user, qs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})


class DonorMyDonationsView(generics.ListAPIView):
    """Donor portal — donations matching the authenticated user's email."""

    permission_classes = [require_permission("donations.view")]
    serializer_class = DonationSerializer

    def get_queryset(self):
        email = self.request.user.email.lower()
        return Donation.objects.filter(
            is_deleted=False,
            donor_email__iexact=email,
            status="COMPLETED",
        ).select_related("category").order_by("-paid_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            return Response({"success": True, "data": response.data})
        return Response({"success": True, "data": response.data})
