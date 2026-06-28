from rest_framework import serializers

from apps.donations.models import Donation, DonationCategory, DonationReceipt


class DonationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationCategory
        fields = ("id", "code", "name", "description", "min_amount", "is_active")


class DonationInitiateSerializer(serializers.Serializer):
    category_code = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    donor_name = serializers.CharField(max_length=200)
    donor_email = serializers.EmailField(required=False, allow_blank=True)
    donor_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    pan_number = serializers.CharField(required=False, allow_blank=True, max_length=10)
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    sponsored_student_id = serializers.UUIDField(required=False, allow_null=True)
    sponsored_acharya_id = serializers.UUIDField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=64)


class DonationConfirmSerializer(serializers.Serializer):
    donation_id = serializers.UUIDField()
    razorpay_order_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_payment_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_signature = serializers.CharField(required=False, allow_blank=True)


class DonationReceiptSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = DonationReceipt
        fields = (
            "id",
            "receipt_number",
            "registration_12a",
            "registration_80g",
            "download_url",
            "created_at",
        )

    def get_download_url(self, obj):
        from apps.core.media_storage import MediaStorageService

        return MediaStorageService.get_stream_url(
            obj.pdf_s3_bucket,
            obj.pdf_s3_key,
            "application/pdf",
            f"{obj.receipt_number}.pdf",
            inline=False,
        )


class DonationSerializer(serializers.ModelSerializer):
    category = DonationCategorySerializer(read_only=True)
    receipt = DonationReceiptSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = (
            "id",
            "donation_number",
            "category",
            "branch_id",
            "sponsored_student_id",
            "donor_name",
            "donor_email",
            "donor_phone",
            "pan_number",
            "amount",
            "currency",
            "status",
            "paid_at",
            "receipt",
            "created_at",
        )
