"""
Custom exception handlers for consistent API error responses.

Provides standardized error formatting for different types of exceptions.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    
    Handles common exceptions and formats them with appropriate HTTP status codes
    and user-friendly error messages.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # DRF handled the exception, format the response consistently
        custom_response_data = {
            'error': True,
            'message': _get_error_message(exc, response.data),
            'details': response.data,
            'status_code': response.status_code
        }
        
        response.data = custom_response_data
        return response
    
    # Handle exceptions that DRF doesn't handle by default
    if isinstance(exc, DjangoValidationError):
        return _handle_validation_error(exc)
    elif isinstance(exc, Http404):
        return _handle_not_found_error(exc)
    elif isinstance(exc, PermissionError):
        return _handle_permission_error(exc)
    
    # Log unhandled exceptions
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return None to fall back to Django's default 500 error handling
    return None


def _get_error_message(exc, response_data):
    """
    Extract a user-friendly error message from the exception and response data.
    """
    # Try to get message from various possible locations
    if isinstance(response_data, dict):
        # Check for common error message fields
        for field in ['detail', 'message', 'error']:
            if field in response_data:
                message = response_data[field]
                if isinstance(message, list) and message:
                    return str(message[0])
                elif isinstance(message, str):
                    return message
        
        # If it's a field validation error, format nicely
        if any(key not in ['detail', 'message', 'error'] for key in response_data.keys()):
            field_errors = []
            for field, errors in response_data.items():
                if isinstance(errors, list):
                    field_errors.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    field_errors.append(f"{field}: {str(errors)}")
            return '; '.join(field_errors)
    
    # Fall back to exception string representation
    return str(exc)


def _handle_validation_error(exc):
    """
    Handle Django ValidationError exceptions.
    """
    if hasattr(exc, 'message_dict'):
        # Field-specific validation errors
        details = exc.message_dict
        message = _get_error_message(exc, details)
    elif hasattr(exc, 'messages'):
        # General validation errors
        details = {'non_field_errors': exc.messages}
        message = '; '.join(exc.messages)
    else:
        details = {'non_field_errors': [str(exc)]}
        message = str(exc)
    
    return Response(
        {
            'error': True,
            'message': message,
            'details': details,
            'status_code': status.HTTP_422_UNPROCESSABLE_ENTITY
        },
        status=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def _handle_not_found_error(exc):
    """
    Handle Http404 exceptions.
    """
    return Response(
        {
            'error': True,
            'message': _('Resource not found.'),
            'details': {'detail': str(exc)},
            'status_code': status.HTTP_404_NOT_FOUND
        },
        status=status.HTTP_404_NOT_FOUND
    )


def _handle_permission_error(exc):
    """
    Handle PermissionError exceptions.
    """
    return Response(
        {
            'error': True,
            'message': _('Permission denied.'),
            'details': {'detail': str(exc)},
            'status_code': status.HTTP_403_FORBIDDEN
        },
        status=status.HTTP_403_FORBIDDEN
    )