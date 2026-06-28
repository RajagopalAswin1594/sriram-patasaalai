"""Formal application status state machine for Feature 1.2."""

from apps.admissions.models import ApplicationStatus
from apps.core.exceptions import ConflictError, DomainError

# Epic review states: Pending → Approved | Rejected
REVIEW_PENDING_STATUSES = frozenset({ApplicationStatus.PENDING})
REVIEW_TERMINAL_STATUSES = frozenset({ApplicationStatus.APPROVED, ApplicationStatus.REJECTED})

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    ApplicationStatus.DRAFT: frozenset({ApplicationStatus.PAYMENT_PENDING}),
    ApplicationStatus.PAYMENT_PENDING: frozenset({ApplicationStatus.PENDING}),
    ApplicationStatus.PENDING: frozenset({ApplicationStatus.APPROVED, ApplicationStatus.REJECTED}),
    ApplicationStatus.APPROVED: frozenset(),
    ApplicationStatus.REJECTED: frozenset(),
    # Legacy alias support during migration window
    "UNDER_REVIEW": frozenset({ApplicationStatus.APPROVED, ApplicationStatus.REJECTED}),
}


def can_transition(from_status: str, to_status: str) -> bool:
    if from_status == to_status:
        return True
    return to_status in ALLOWED_TRANSITIONS.get(from_status, frozenset())


def assert_transition(from_status: str, to_status: str):
    if not can_transition(from_status, to_status):
        raise ConflictError(f"Cannot transition from {from_status} to {to_status}.")


def normalize_review_status(status: str) -> str:
    """Map legacy UNDER_REVIEW to PENDING."""
    if status == "UNDER_REVIEW":
        return ApplicationStatus.PENDING
    return status


def is_reviewable(status: str) -> bool:
    return normalize_review_status(status) in REVIEW_PENDING_STATUSES


def assert_review_decision(status: str):
    if status not in REVIEW_TERMINAL_STATUSES:
        raise DomainError("Review decision must be APPROVED or REJECTED.")
