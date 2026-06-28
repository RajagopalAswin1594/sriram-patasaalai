import logging
import re

logger = logging.getLogger(__name__)


def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 4:
        return "****"
    return f"{'*' * (len(phone) - 4)}{phone[-4:]}"


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "****"
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"


def mask_address_line(line: str) -> str:
    if not line:
        return ""
    if len(line) <= 8:
        return "***"
    return f"{line[:4]}...{line[-4:]}"


class PrivacyMaskingService:
    """GDPR-minded field masking for list views and lower-privilege access."""

    PII_FIELDS = (
        "parent_phone",
        "parent_email",
        "address_line_1",
        "address_line_2",
        "parent_name",
    )

    @classmethod
    def mask_application_data(cls, data: dict, reveal: bool = False) -> dict:
        if reveal:
            return data
        masked = data.copy()
        if "parent_phone" in masked:
            masked["parent_phone"] = mask_phone(str(masked.get("parent_phone", "")))
        if "parent_email" in masked:
            masked["parent_email"] = mask_email(str(masked.get("parent_email", "")))
        if "address_line_1" in masked:
            masked["address_line_1"] = mask_address_line(str(masked.get("address_line_1", "")))
        if "address_line_2" in masked and masked["address_line_2"]:
            masked["address_line_2"] = mask_address_line(str(masked.get("address_line_2", "")))
        if "parent_name" in masked and masked["parent_name"]:
            parts = str(masked["parent_name"]).split()
            masked["parent_name"] = f"{parts[0][0]}***" if parts else "***"
        masked["pii_masked"] = True
        return masked

    @classmethod
    def user_can_view_full_pii(cls, user) -> bool:
        from apps.rbac.services import PermissionService

        return PermissionService.user_has_permission(user, "admissions.change") or PermissionService.user_has_permission(
            user, "admissions.approve"
        )
