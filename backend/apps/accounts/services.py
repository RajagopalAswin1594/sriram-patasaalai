import hashlib
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken

from apps.accounts.models import (
    AccountStatus,
    PasswordResetToken,
    RefreshToken,
    RefreshTokenRevokeReason,
    User,
    UserType,
)
from apps.audit.models import AuthenticationEvent, AuthEventOutcome, AuthEventType
from apps.audit.services import record_auth_event
from apps.core.exceptions import ConflictError, DomainError, NotFoundError


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def get_client_meta(request):
    return {
        "ip_address": request.META.get("REMOTE_ADDR"),
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        "device_fingerprint": request.META.get("HTTP_X_DEVICE_FINGERPRINT", ""),
    }


class AuthenticationService:
    @staticmethod
    def _issue_tokens(user, request, branch_id=None):
        refresh = JWTRefreshToken.for_user(user)
        jti = uuid.UUID(str(refresh["jti"]))
        meta = get_client_meta(request)
        RefreshToken.objects.create(
            user=user,
            token_jti=jti,
            token_hash=hash_token(str(refresh)),
            issued_at=timezone.now(),
            expires_at=timezone.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            ip_address=meta["ip_address"],
            user_agent=meta["user_agent"],
            device_fingerprint=meta["device_fingerprint"],
        )
        access = refresh.access_token
        if branch_id:
            access["branch_id"] = str(branch_id)
        access["user_type"] = user.user_type
        return {
            "access": str(access),
            "refresh": str(refresh),
        }

    @classmethod
    @transaction.atomic
    def login(cls, email, password, request, branch_id=None):
        meta = get_client_meta(request)
        normalized_email = User.objects.normalize_email(email).lower()
        try:
            user = User.all_objects.get(email=normalized_email)
        except User.DoesNotExist:
            record_auth_event(
                event_type=AuthEventType.LOGIN_ATTEMPT,
                outcome=AuthEventOutcome.FAILURE,
                email_attempted=normalized_email,
                failure_reason="INVALID_CREDENTIALS",
                branch_id=branch_id,
                **meta,
            )
            raise DomainError("Invalid credentials.")

        if user.is_deleted or user.account_status in (AccountStatus.INACTIVE, AccountStatus.SUSPENDED):
            record_auth_event(
                user=user,
                event_type=AuthEventType.LOGIN_ATTEMPT,
                outcome=AuthEventOutcome.BLOCKED,
                failure_reason="ACCOUNT_INACTIVE",
                branch_id=branch_id,
                **meta,
            )
            raise DomainError("Account is not active.")

        if user.is_account_locked:
            record_auth_event(
                user=user,
                event_type=AuthEventType.LOGIN_ATTEMPT,
                outcome=AuthEventOutcome.BLOCKED,
                failure_reason="ACCOUNT_LOCKED",
                branch_id=branch_id,
                **meta,
            )
            raise DomainError("Account is temporarily locked.")

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                user.account_status = AccountStatus.LOCKED
                user.locked_until = timezone.now() + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
                record_auth_event(
                    user=user,
                    event_type=AuthEventType.ACCOUNT_LOCKED,
                    outcome=AuthEventOutcome.SUCCESS,
                    branch_id=branch_id,
                    **meta,
                )
            user.save(update_fields=["failed_login_attempts", "account_status", "locked_until", "updated_at"])
            record_auth_event(
                user=user,
                event_type=AuthEventType.LOGIN_ATTEMPT,
                outcome=AuthEventOutcome.FAILURE,
                failure_reason="INVALID_CREDENTIALS",
                branch_id=branch_id,
                **meta,
            )
            raise DomainError("Invalid credentials.")

        if user.account_status == AccountStatus.PENDING_VERIFICATION:
            record_auth_event(
                user=user,
                event_type=AuthEventType.LOGIN_ATTEMPT,
                outcome=AuthEventOutcome.BLOCKED,
                failure_reason="EMAIL_NOT_VERIFIED",
                branch_id=branch_id,
                **meta,
            )
            raise DomainError("Email verification required.")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = timezone.now()
        user.save(update_fields=["failed_login_attempts", "locked_until", "last_login", "updated_at"])

        tokens = cls._issue_tokens(user, request, branch_id=branch_id)
        record_auth_event(
            user=user,
            event_type=AuthEventType.LOGIN_SUCCESS,
            outcome=AuthEventOutcome.SUCCESS,
            branch_id=branch_id,
            **meta,
        )
        return user, tokens

    @classmethod
    @transaction.atomic
    def refresh(cls, raw_refresh_token, request):
        meta = get_client_meta(request)
        token_hash = hash_token(raw_refresh_token)
        stored = (
            RefreshToken.objects.filter(token_hash=token_hash, revoked_at__isnull=True)
            .select_related("user")
            .first()
        )
        if not stored or not stored.is_active:
            record_auth_event(
                event_type=AuthEventType.TOKEN_REFRESH,
                outcome=AuthEventOutcome.FAILURE,
                failure_reason="TOKEN_EXPIRED",
                **meta,
            )
            raise DomainError("Invalid or expired refresh token.")

        user = stored.user
        if not user.can_authenticate():
            record_auth_event(
                user=user,
                event_type=AuthEventType.TOKEN_REFRESH,
                outcome=AuthEventOutcome.BLOCKED,
                failure_reason="ACCOUNT_INACTIVE",
                refresh_token_jti=stored.token_jti,
                **meta,
            )
            raise DomainError("Account is not active.")

        new_refresh = JWTRefreshToken.for_user(user)
        new_jti = uuid.UUID(str(new_refresh["jti"]))
        stored.revoked_at = timezone.now()
        stored.revoked_reason = RefreshTokenRevokeReason.ROTATION
        stored.replaced_by_jti = new_jti
        stored.save(update_fields=["revoked_at", "revoked_reason", "replaced_by_jti", "updated_at"])

        RefreshToken.objects.create(
            user=user,
            token_jti=new_jti,
            token_hash=hash_token(str(new_refresh)),
            issued_at=timezone.now(),
            expires_at=timezone.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            ip_address=meta["ip_address"],
            user_agent=meta["user_agent"],
            device_fingerprint=meta["device_fingerprint"],
        )

        record_auth_event(
            user=user,
            event_type=AuthEventType.TOKEN_REFRESH,
            outcome=AuthEventOutcome.SUCCESS,
            refresh_token_jti=new_jti,
            **meta,
        )
        return {
            "access": str(new_refresh.access_token),
            "refresh": str(new_refresh),
        }

    @classmethod
    @transaction.atomic
    def logout(cls, raw_refresh_token, request):
        meta = get_client_meta(request)
        token_hash = hash_token(raw_refresh_token)
        stored = RefreshToken.objects.filter(token_hash=token_hash, revoked_at__isnull=True).select_related("user").first()
        if stored:
            stored.revoked_at = timezone.now()
            stored.revoked_reason = RefreshTokenRevokeReason.LOGOUT
            stored.save(update_fields=["revoked_at", "revoked_reason", "updated_at"])
            record_auth_event(
                user=stored.user,
                event_type=AuthEventType.LOGOUT,
                outcome=AuthEventOutcome.SUCCESS,
                refresh_token_jti=stored.token_jti,
                **meta,
            )

    @classmethod
    @transaction.atomic
    def request_password_reset(cls, email, request):
        meta = get_client_meta(request)
        normalized_email = User.objects.normalize_email(email).lower()
        user = User.objects.filter(email=normalized_email).first()
        raw_token = secrets.token_urlsafe(48)
        if user:
            PasswordResetToken.objects.filter(user=user, used_at__isnull=True, expires_at__gt=timezone.now()).update(
                used_at=timezone.now()
            )
            PasswordResetToken.objects.create(
                user=user,
                token_hash=hash_token(raw_token),
                expires_at=timezone.now() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_HOURS),
                requested_ip=meta["ip_address"],
                requested_user_agent=meta["user_agent"],
            )
            record_auth_event(
                user=user,
                event_type=AuthEventType.PASSWORD_RESET_REQUEST,
                outcome=AuthEventOutcome.SUCCESS,
                **meta,
            )
        return raw_token if user else None

    @classmethod
    @transaction.atomic
    def confirm_password_reset(cls, raw_token, new_password, request):
        meta = get_client_meta(request)
        token_hash = hash_token(raw_token)
        reset_token = PasswordResetToken.objects.filter(token_hash=token_hash).select_related("user").first()
        if not reset_token or not reset_token.is_valid:
            record_auth_event(
                event_type=AuthEventType.PASSWORD_RESET_COMPLETE,
                outcome=AuthEventOutcome.FAILURE,
                failure_reason="TOKEN_EXPIRED",
                **meta,
            )
            raise DomainError("Invalid or expired reset token.")

        user = reset_token.user
        validate_password(new_password, user)
        user.set_password(new_password)
        user.last_password_change_at = timezone.now()
        user.must_change_password = False
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.account_status == AccountStatus.LOCKED:
            user.account_status = AccountStatus.ACTIVE
        user.save()
        reset_token.used_at = timezone.now()
        reset_token.save(update_fields=["used_at", "updated_at"])
        cls.revoke_all_sessions(user, RefreshTokenRevokeReason.PASSWORD_CHANGE)
        record_auth_event(
            user=user,
            event_type=AuthEventType.PASSWORD_RESET_COMPLETE,
            outcome=AuthEventOutcome.SUCCESS,
            **meta,
        )

    @classmethod
    def revoke_all_sessions(cls, user, reason=RefreshTokenRevokeReason.ADMIN_REVOKE):
        RefreshToken.objects.filter(user=user, revoked_at__isnull=True).update(
            revoked_at=timezone.now(),
            revoked_reason=reason,
        )

    @classmethod
    @transaction.atomic
    def change_password(cls, user, current_password, new_password, request):
        meta = get_client_meta(request)
        if not user.check_password(current_password):
            record_auth_event(
                user=user,
                event_type=AuthEventType.PASSWORD_CHANGE,
                outcome=AuthEventOutcome.FAILURE,
                failure_reason="INVALID_CREDENTIALS",
                **meta,
            )
            raise DomainError("Current password is incorrect.")

        validate_password(new_password, user)
        user.set_password(new_password)
        user.last_password_change_at = timezone.now()
        user.must_change_password = False
        user.save()
        cls.revoke_all_sessions(user, RefreshTokenRevokeReason.PASSWORD_CHANGE)
        record_auth_event(
            user=user,
            event_type=AuthEventType.PASSWORD_CHANGE,
            outcome=AuthEventOutcome.SUCCESS,
            **meta,
        )


class AccountStatusService:
    ALLOWED_TRANSITIONS = {
        AccountStatus.PENDING_VERIFICATION: {AccountStatus.ACTIVE, AccountStatus.INACTIVE},
        AccountStatus.ACTIVE: {AccountStatus.INACTIVE, AccountStatus.SUSPENDED, AccountStatus.LOCKED},
        AccountStatus.LOCKED: {AccountStatus.ACTIVE},
        AccountStatus.INACTIVE: {AccountStatus.ACTIVE},
        AccountStatus.SUSPENDED: {AccountStatus.ACTIVE},
    }

    @classmethod
    @transaction.atomic
    def transition(cls, user, new_status, actor, request=None):
        if new_status == user.account_status:
            return user
        allowed = cls.ALLOWED_TRANSITIONS.get(user.account_status, set())
        if new_status not in allowed and not (new_status == AccountStatus.ACTIVE and user.account_status == AccountStatus.LOCKED):
            raise ConflictError(f"Cannot transition from {user.account_status} to {new_status}.")

        old_status = user.account_status
        user.account_status = new_status
        if new_status == AccountStatus.ACTIVE:
            user.failed_login_attempts = 0
            user.locked_until = None
        user.save(update_fields=["account_status", "failed_login_attempts", "locked_until", "updated_at"])

        meta = get_client_meta(request) if request else {}
        record_auth_event(
            user=user,
            event_type=AuthEventType.ACCOUNT_STATUS_CHANGE,
            outcome=AuthEventOutcome.SUCCESS,
            metadata={"old_status": old_status, "new_status": new_status, "actor_id": str(actor.id)},
            **meta,
        )
        if new_status in (AccountStatus.INACTIVE, AccountStatus.SUSPENDED):
            AuthenticationService.revoke_all_sessions(user)
        return user

    @classmethod
    @transaction.atomic
    def verify_email(cls, user):
        user.email_verified_at = timezone.now()
        if user.account_status == AccountStatus.PENDING_VERIFICATION:
            user.account_status = AccountStatus.ACTIVE
        user.save(update_fields=["email_verified_at", "account_status", "updated_at"])
        return user


PROFILE_MODEL_MAP = {
    UserType.STUDENT: "student_profile",
    UserType.PARENT: "parent_profile",
    UserType.ACHARYA: "acharya_profile",
    UserType.BRANCH_ADMIN: "branch_admin_profile",
    UserType.DONOR: "donor_profile",
    UserType.HOSTEL_WARDEN: "hostel_warden_profile",
}


def get_type_profile(user):
    attr = PROFILE_MODEL_MAP.get(user.user_type)
    if not attr:
        return None
    return getattr(user, attr, None)
