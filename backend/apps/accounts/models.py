from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import AuditableModel


class UserType(models.TextChoices):
    STUDENT = "STUDENT", "Student"
    PARENT = "PARENT", "Parent"
    ACHARYA = "ACHARYA", "Acharya"
    BRANCH_ADMIN = "BRANCH_ADMIN", "Branch Admin"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    DONOR = "DONOR", "Donor"
    HOSTEL_WARDEN = "HOSTEL_WARDEN", "Hostel Warden"
    ALUMNI = "ALUMNI", "Alumni"


class AccountStatus(models.TextChoices):
    PENDING_VERIFICATION = "PENDING_VERIFICATION", "Pending Verification"
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"
    LOCKED = "LOCKED", "Locked"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("account_status", AccountStatus.PENDING_VERIFICATION)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("user_type", UserType.SUPER_ADMIN)
        extra_fields.setdefault("account_status", AccountStatus.ACTIVE)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("email_verified_at", timezone.now())
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, AuditableModel):
    email = models.EmailField(unique=True, db_index=True)
    user_type = models.CharField(max_length=20, choices=UserType.choices, db_index=True)
    account_status = models.CharField(
        max_length=30,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING_VERIFICATION,
        db_index=True,
    )
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_password_change_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["user_type"]

    objects = UserManager()
    all_objects = models.Manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_superuser=False) | models.Q(user_type=UserType.SUPER_ADMIN),
                name="superuser_must_be_super_admin",
            ),
        ]

    def __str__(self):
        return self.email

    @property
    def is_account_locked(self):
        return self.locked_until and self.locked_until > timezone.now()

    def can_authenticate(self):
        return self.account_status == AccountStatus.ACTIVE and not self.is_deleted and not self.is_account_locked


class UserProfile(AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    avatar_url = models.URLField(blank=True)
    preferred_language = models.CharField(max_length=10, blank=True, default="en")
    timezone = models.CharField(max_length=50, blank=True, default="UTC")

    def __str__(self):
        return self.display_name or f"{self.first_name} {self.last_name}".strip()


class RelationshipType(models.TextChoices):
    FATHER = "FATHER", "Father"
    MOTHER = "MOTHER", "Mother"
    GUARDIAN = "GUARDIAN", "Guardian"


class StudentProfile(AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    admission_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)


class ParentProfile(AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    relationship_type = models.CharField(max_length=20, choices=RelationshipType.choices)


class AcharyaProfile(AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="acharya_profile")
    employee_code = models.CharField(max_length=50, blank=True)
    specialization = models.CharField(max_length=200, blank=True)


class BranchAdminProfile(AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="branch_admin_profile")
    designation = models.CharField(max_length=150, blank=True)


class DonorProfile(AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="donor_profile")
    organization_name = models.CharField(max_length=200, blank=True)
    pan_or_tax_id = models.CharField(max_length=50, blank=True)


class HostelWardenProfile(AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hostel_warden_profile")
    employee_code = models.CharField(max_length=50, blank=True)


class RefreshTokenRevokeReason(models.TextChoices):
    LOGOUT = "LOGOUT", "Logout"
    ROTATION = "ROTATION", "Rotation"
    ADMIN_REVOKE = "ADMIN_REVOKE", "Admin Revoke"
    COMPROMISED = "COMPROMISED", "Compromised"
    PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"


class RefreshToken(AuditableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_jti = models.UUIDField(unique=True, db_index=True)
    token_hash = models.CharField(max_length=128)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True, db_index=True)
    revoked_reason = models.CharField(max_length=30, choices=RefreshTokenRevokeReason.choices, blank=True)
    replaced_by_jti = models.UUIDField(null=True, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
        ]

    @property
    def is_active(self):
        return self.revoked_at is None and self.expires_at > timezone.now()


class PasswordResetToken(AuditableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    requested_ip = models.GenericIPAddressField(null=True, blank=True)
    requested_user_agent = models.TextField(blank=True)

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()
