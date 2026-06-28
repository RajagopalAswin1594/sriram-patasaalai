import uuid

from django.utils.deprecation import MiddlewareMixin

from apps.core.context import clear_audit_context, set_audit_context, get_correlation_id


class AuditContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        clear_audit_context()
        branch = getattr(request, "branch", None)
        set_audit_context(
            actor=getattr(request, "user", None) if getattr(request, "user", None) and request.user.is_authenticated else None,
            branch=branch,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            correlation_id=str(get_correlation_id()),
            metadata={"path": request.path, "method": request.method},
        )

    def process_response(self, request, response):
        clear_audit_context()
        return response
