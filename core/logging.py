"""
Structured logging configuration and helpers for the Django application.

This module provides structured JSON-based logging with contextual information
including request ID, user ID, and organization ID for better observability.
"""

import threading
import uuid
from typing import Dict, Optional

import structlog
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin

# Thread-local storage for request context
_local = threading.local()


def set_request_context(
    request_id: str, user_id: Optional[str] = None, org_id: Optional[str] = None
):
    """
    Set the request context in thread-local storage.

    Args:
        request_id: Unique identifier for the request
        user_id: ID of the authenticated user (if any)
        org_id: ID of the user's default organization (if any)
    """
    _local.request_context = {
        "request_id": request_id,
        "user_id": user_id,
        "org_id": org_id,
    }


def get_request_context() -> Dict[str, Optional[str]]:
    """
    Get the current request context from thread-local storage.

    Returns:
        Dictionary containing request_id, user_id, and org_id
    """
    return getattr(
        _local,
        "request_context",
        {
            "request_id": None,
            "user_id": None,
            "org_id": None,
        },
    )


def clear_request_context():
    """Clear the request context from thread-local storage."""
    if hasattr(_local, "request_context"):
        delattr(_local, "request_context")


def add_request_context(logger, method_name, event_dict):
    """
    Structlog processor to add request context to log entries.

    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The event dictionary to be logged

    Returns:
        Updated event dictionary with request context
    """
    context = get_request_context()
    event_dict.update(context)
    return event_dict


def extract_user_context(request: HttpRequest) -> tuple[Optional[str], Optional[str]]:
    """
    Extract user ID and organization ID from the request.

    Args:
        request: Django HTTP request object

    Returns:
        Tuple of (user_id, org_id)
    """
    user_id = None
    org_id = None

    if hasattr(request, "user") and request.user.is_authenticated:
        user_id = str(request.user.id)

        # Get the user's default organization if available
        try:
            default_org = request.user.get_default_organization()
            if default_org:
                org_id = str(default_org.id)
        except Exception:
            # Silently handle any errors in getting organization
            pass

    return user_id, org_id


def get_structured_logger(name: str = None):
    """
    Get a structured logger instance.

    Args:
        name: Logger name (defaults to caller's module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class StructuredLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to generate request IDs and set request context for structured logging.

    This middleware:
    1. Generates a unique request ID for each request
    2. Extracts user and organization context
    3. Stores context in thread-local storage
    4. Adds the request ID to the response headers
    5. Cleans up context after request processing
    """

    def process_request(self, request):
        """Process the incoming request to set up logging context."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id

        # Extract user and organization context
        user_id, org_id = extract_user_context(request)

        # Set context in thread-local storage
        set_request_context(request_id, user_id, org_id)

        # Log the request
        logger = get_structured_logger(__name__)
        logger.info(
            "Request started",
            method=request.method,
            path=request.path,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            remote_addr=request.META.get("REMOTE_ADDR", ""),
        )

    def process_response(self, request, response):
        """Process the response to add headers and clean up context."""
        # Add request ID to response headers
        if hasattr(request, "request_id"):
            response["X-Request-ID"] = request.request_id

        # Log the response
        logger = get_structured_logger(__name__)
        logger.info(
            "Request completed",
            status_code=response.status_code,
            content_type=response.get("Content-Type", ""),
        )

        # Clean up thread-local storage
        clear_request_context()

        return response

    def process_exception(self, request, exception):
        """Process exceptions to log them with context."""
        logger = get_structured_logger(__name__)
        logger.error(
            "Request failed with exception",
            exception_type=exception.__class__.__name__,
            exception_message=str(exception),
            exc_info=True,
        )

        # Clean up thread-local storage
        clear_request_context()


def configure_structlog():
    """Configure structlog for the Django application."""
    import os

    # Use JSON renderer in production, console renderer in development
    use_json = os.environ.get("DJANGO_ENV") in ["production", "staging"]

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_request_context,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            (
                structlog.processors.JSONRenderer()
                if use_json
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # DEBUG level
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
