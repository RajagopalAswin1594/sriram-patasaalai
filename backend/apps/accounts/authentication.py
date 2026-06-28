import uuid

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.branches.models import Branch
from apps.core.context import set_audit_context


class BranchJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return result

        user, validated_token = result
        branch_id = request.META.get(settings.BRANCH_HEADER) or validated_token.get("branch_id")
        request.branch = None
        request.branch_id = None

        if branch_id:
            try:
                branch_uuid = uuid.UUID(str(branch_id))
                request.branch = Branch.objects.filter(id=branch_uuid, is_deleted=False).first()
                request.branch_id = branch_uuid if request.branch else None
            except (ValueError, TypeError):
                raise InvalidToken("Invalid branch context.")

        set_audit_context(
            actor=user,
            branch=request.branch,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return user, validated_token
