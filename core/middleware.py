from django.middleware.csrf import CsrfViewMiddleware

from .signals import set_current_user


class CurrentUserMiddleware:
    """
    Middleware to capture the current user and store it in thread-local storage.

    This allows the signals to access the current user for automatic assignment
    of created_by and updated_by fields.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set the current user in thread-local storage
        if hasattr(request, "user"):
            set_current_user(request.user)
        else:
            set_current_user(None)

        response = self.get_response(request)

        # Clean up thread-local storage
        set_current_user(None)

        return response


class TokenBasedCSRFExemptMiddleware(CsrfViewMiddleware):
    """
    CSRF middleware that exempts API endpoints using token authentication.

    For API endpoints using token authentication, CSRF protection is not
    necessary since tokens provide their own security mechanism.
    This middleware exempts API URLs from CSRF checks when using token auth.
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Check if this is an API endpoint
        if request.path.startswith("/api/"):
            # Check if using token authentication
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Token "):
                # Exempt from CSRF for token-based API requests
                return None

        # Use default CSRF processing for all other requests
        return super().process_view(request, callback, callback_args, callback_kwargs)
