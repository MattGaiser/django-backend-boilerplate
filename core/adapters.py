"""
Django Allauth custom adapters for SSO integration.

This module provides custom adapters to handle social authentication
and account management with organization scoping.
"""

import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for handling email-based authentication.

    Provides custom logic for account creation, email confirmation,
    and other account-related operations.
    """

    def is_open_for_signup(self, request):
        """
        Check if signups are allowed.

        Returns:
            bool: True if signups are allowed, False otherwise
        """
        # Allow signups by default, but this can be customized
        # to check for organization invites, domain restrictions, etc.
        return True

    def save_user(self, request, user, form, commit=True):
        """
        Save user with custom logic.

        Args:
            request: The current request
            user: User instance to save
            form: The signup form
            commit: Whether to save to database

        Returns:
            User: The saved user instance
        """
        user = super().save_user(request, user, form, commit=False)

        # Add custom logic here if needed
        # For example, set user language based on request headers
        if hasattr(request, "LANGUAGE_CODE"):
            user.language = request.LANGUAGE_CODE

        if commit:
            user.save()

        logger.info(f"User created via email signup: {user.email}")
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for handling SSO authentication.

    Provides custom logic for social account creation, organization scoping,
    and other social authentication operations.
    """

    def is_open_for_signup(self, request, sociallogin):
        """
        Check if social signups are allowed.

        Args:
            request: The current request
            sociallogin: Social login instance

        Returns:
            bool: True if social signups are allowed, False otherwise
        """
        # Allow social signups by default
        # This can be customized based on:
        # - Email domain restrictions
        # - Organization invitations
        # - Provider-specific rules
        return True

    def pre_social_login(self, request, sociallogin):
        """
        Custom logic before social login/signup.

        Args:
            request: The current request
            sociallogin: Social login instance
        """
        # Extract email from social account
        email = None
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get("email")

        if not email:
            logger.warning(
                f"No email found in social login data for provider {sociallogin.account.provider}"
            )
            return

        # Log the social login attempt
        logger.info(f"Social login attempt: {email} via {sociallogin.account.provider}")

        # Check if user exists with this email
        from core.models import User

        try:
            existing_user = User.objects.get(email=email)
            if not sociallogin.is_existing:
                # Connect the social account to existing user
                sociallogin.connect(request, existing_user)
                logger.info(f"Connected social account to existing user: {email}")
        except User.DoesNotExist:
            # New user - will be handled by save_user
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Save user from social login with custom logic.

        Args:
            request: The current request
            sociallogin: Social login instance
            form: Optional form data

        Returns:
            User: The saved user instance
        """
        user = super().save_user(request, sociallogin, form)

        # Extract additional user information from social account
        extra_data = sociallogin.account.extra_data
        provider = sociallogin.account.provider

        # Set full_name from social account if not set
        if not user.full_name and extra_data:
            name = extra_data.get("name") or extra_data.get("displayName")
            if name:
                user.full_name = name

        # Set language based on locale from social account
        if extra_data and extra_data.get("locale"):
            locale = extra_data.get("locale", "").lower()
            if locale.startswith("fr"):
                user.language = "fr"
            else:
                user.language = "en"

        user.save()

        # TODO: Organization scoping logic
        # This is where you would implement organization assignment
        # based on email domain, invitations, or other business rules
        self._handle_organization_assignment(user, sociallogin)

        logger.info(f"User created via {provider} SSO: {user.email}")
        return user

    def _handle_organization_assignment(self, user, sociallogin):
        """
        Handle organization assignment for new social users.

        Args:
            user: The user instance
            sociallogin: Social login instance
        """
        # This is a placeholder for organization assignment logic
        # In a real implementation, you might:
        # 1. Check for pending invitations based on email
        # 2. Assign to organization based on email domain
        # 3. Create a default personal organization
        # 4. Require manual organization assignment

        # For now, we'll just log that no organization was assigned
        logger.info(f"No organization assignment implemented for user: {user.email}")
        # You could create a default organization or require assignment later

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Get redirect URL after connecting a social account.

        Args:
            request: The current request
            socialaccount: Social account instance

        Returns:
            str: URL to redirect to after connection
        """
        # Redirect to user profile or dashboard after connecting
        return "/accounts/profile/"  # Customize as needed

    def authentication_error(
        self, request, provider_id, error=None, exception=None, extra_context=None
    ):
        """
        Handle authentication errors.

        Args:
            request: The current request
            provider_id: Social provider ID
            error: Error code
            exception: Exception instance
            extra_context: Additional context
        """
        logger.error(f"Social authentication error for {provider_id}: {error}")

        # Add user-friendly error message
        if error == "access_denied":
            messages.error(request, _("Access was denied. Please try again."))
        elif error == "invalid_request":
            messages.error(
                request, _("Invalid request. Please contact support if this persists.")
            )
        else:
            messages.error(
                request,
                _("Authentication failed. Please try again or contact support."),
            )

        # Note: Parent class doesn't have authentication_error method
        # This method is our custom implementation
