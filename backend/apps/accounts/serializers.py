from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import (
    AccountStatus,
    AcharyaProfile,
    BranchAdminProfile,
    DonorProfile,
    HostelWardenProfile,
    ParentProfile,
    StudentProfile,
    User,
    UserProfile,
    UserType,
)
from apps.accounts.services import PROFILE_MODEL_MAP


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "first_name",
            "last_name",
            "display_name",
            "phone",
            "phone_verified_at",
            "avatar_url",
            "preferred_language",
            "timezone",
        ]
        read_only_fields = ["phone_verified_at"]


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["admission_number", "date_of_birth"]


class ParentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentProfile
        fields = ["relationship_type"]


class AcharyaProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcharyaProfile
        fields = ["employee_code", "specialization"]


class BranchAdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchAdminProfile
        fields = ["designation"]


class DonorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorProfile
        fields = ["organization_name", "pan_or_tax_id"]


class HostelWardenProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelWardenProfile
        fields = ["employee_code"]


TYPE_PROFILE_SERIALIZERS = {
    UserType.STUDENT: StudentProfileSerializer,
    UserType.PARENT: ParentProfileSerializer,
    UserType.ACHARYA: AcharyaProfileSerializer,
    UserType.BRANCH_ADMIN: BranchAdminProfileSerializer,
    UserType.DONOR: DonorProfileSerializer,
    UserType.HOSTEL_WARDEN: HostelWardenProfileSerializer,
}


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    type_profile = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "user_type",
            "account_status",
            "email_verified_at",
            "last_login",
            "must_change_password",
            "profile",
            "type_profile",
            "roles",
            "branches",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email_verified_at",
            "last_login",
            "created_at",
            "updated_at",
        ]

    def get_type_profile(self, obj):
        attr = PROFILE_MODEL_MAP.get(obj.user_type)
        if not attr:
            return None
        profile = getattr(obj, attr, None)
        if not profile:
            return None
        serializer_class = TYPE_PROFILE_SERIALIZERS.get(obj.user_type)
        return serializer_class(profile).data if serializer_class else None

    def get_roles(self, obj):
        return list(
            obj.role_assignments.filter(is_active=True, is_deleted=False).values(
                "id",
                "role__code",
                "role__name",
                "branch_id",
            )
        )

    def get_branches(self, obj):
        return list(
            obj.branch_memberships.filter(is_active=True, is_deleted=False).values(
                "branch_id",
                "branch__code",
                "branch__name",
                "is_primary",
            )
        )


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12)
    user_type = serializers.ChoiceField(choices=UserType.choices)
    account_status = serializers.ChoiceField(choices=AccountStatus.choices, required=False)
    profile = UserProfileSerializer(required=False)
    type_profile = serializers.DictField(required=False)

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        validate_password(attrs["password"])
        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ["account_status", "must_change_password", "profile"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    branch_id = serializers.UUIDField(required=False, allow_null=True)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=12)

    def validate_password(self, value):
        validate_password(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class AccountStatusSerializer(serializers.Serializer):
    account_status = serializers.ChoiceField(choices=AccountStatus.choices)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_type"] = user.user_type
        return token
