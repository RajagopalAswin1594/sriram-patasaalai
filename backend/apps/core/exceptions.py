from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class DomainError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "domain_error"


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"


class PermissionDeniedError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "permission_denied"


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        detail = response.data
        if isinstance(detail, dict) and "detail" in detail:
            detail = detail["detail"]
        response.data = {
            "success": False,
            "error": {
                "code": getattr(exc, "default_code", "error"),
                "message": detail,
            },
        }
    return response
