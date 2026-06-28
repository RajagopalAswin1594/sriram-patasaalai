from django.db import models

from apps.core.models import AuditableModel


class AlumniProfile(AuditableModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="alumni_profile")
    graduation_year = models.PositiveIntegerField()
    batch_name = models.CharField(max_length=150, blank=True)
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)
    current_city = models.CharField(max_length=100, blank=True)
    current_occupation = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    is_directory_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-graduation_year", "user__profile__first_name"]
        verbose_name_plural = "alumni profiles"

    def __str__(self):
        return f"Alumni {self.user.email}"
