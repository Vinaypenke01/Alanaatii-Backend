"""
Custom exception handler for consistent API error responses.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('apps')


def custom_exception_handler(exc, context):
    """
    Returns errors in a consistent format:
    {
        "error": true,
        "code": "VALIDATION_ERROR",
        "message": "Human-readable summary",
        "details": { ... }  # original DRF details
    }
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    if response is not None:
        error_code = _get_error_code(response.status_code)
        message = _extract_message(response.data)

        response.data = {
            'error': True,
            'code': error_code,
            'message': message,
            'details': response.data if not isinstance(response.data, str) else {'detail': response.data},
        }
    else:
        # Unhandled exception — 500
        logger.exception('Unhandled exception in view', exc_info=exc)
        response = Response(
            {
                'error': True,
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred. Our team has been notified.',
                'details': {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_code(status_code):
    codes = {
        400: 'VALIDATION_ERROR',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        409: 'CONFLICT',
        429: 'RATE_LIMITED',
        500: 'INTERNAL_SERVER_ERROR',
    }
    return codes.get(status_code, 'REQUEST_FAILED')


def _extract_message(data):
    """Pull a readable message from DRF error data."""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        if 'detail' in data:
            detail = data['detail']
            return str(detail) if not isinstance(detail, list) else str(detail[0])
        # Collect first field error
        for key, val in data.items():
            if isinstance(val, list) and val:
                return f"{key}: {val[0]}"
            if isinstance(val, str):
                return f"{key}: {val}"
    if isinstance(data, list) and data:
        return str(data[0])
    return 'Request failed.'
