from django.db import models
from django.utils.text import slugify

from apps.core.models import AuditableModel


class BranchStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    ARCHIVED = "ARCHIVED", "Archived"


class Branch(AuditableModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=BranchStatus.choices, default=BranchStatus.DRAFT)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default="IN")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    is_headquarters = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "branches"
        constraints = [
            models.UniqueConstraint(
                fields=["is_headquarters"],
                condition=models.Q(is_headquarters=True, is_deleted=False, status=BranchStatus.ACTIVE),
                name="unique_active_headquarters",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class UserBranchMembership(AuditableModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="branch_memberships")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="memberships")
    is_primary = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "branch"], name="unique_user_branch_membership"),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.branch.code}"
