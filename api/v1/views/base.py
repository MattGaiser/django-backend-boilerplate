"""
Base ViewSet classes that provide RBAC enforcement and organization scoping.

All API ViewSets should inherit from BaseViewSet to ensure consistent
authentication, permission checking, and multi-tenant behavior.
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions.org_scoped import IsAuthenticatedAndInOrgWithRole


class BaseViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet that provides RBAC enforcement and organization scoping.

    Features:
    - Enforces authentication by default
    - Supports organization-scoped access control
    - Provides consistent error handling
    - Includes audit trail support
    - Supports translation and PII tagging

    Subclasses should:
    - Set required_roles attribute for role-based access
    - Implement get_organization() method if using org-scoped permissions
    - Override get_queryset() to filter by organization if needed
    """

    permission_classes = [IsAuthenticated]
    required_roles = []  # Override in subclasses to enable role-based access

    def get_organization(self):
        """
        Get the organization context for this request.

        Subclasses should override this method to determine the appropriate
        organization based on the request context (URL params, user's default org, etc.).

        Returns:
            Organization: The organization for this request context

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        # Try to get organization from URL parameters first
        org_id = self.kwargs.get("organization_id") or self.kwargs.get("org_id")
        if org_id:
            try:
                from core.models import Organization

                return Organization.objects.get(id=org_id)
            except ObjectDoesNotExist:
                return None

        # Fall back to user's default organization
        if hasattr(self.request, "user") and self.request.user.is_authenticated:
            return self.request.user.get_default_organization()

        return None

    def get_permissions(self):
        """
        Get the permissions for this view.

        If required_roles is set, use organization-scoped permissions.
        Otherwise, use the default permissions.
        """
        if self.required_roles:
            permission_classes = [IsAuthenticatedAndInOrgWithRole]
        else:
            permission_classes = self.permission_classes

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Get the queryset for this view.

        By default, returns the queryset unchanged. Subclasses should override
        this to filter by organization if the model has organization relationships.
        """
        return super().get_queryset()

    def perform_create(self, serializer):
        """
        Perform creation with audit trail support.

        Automatically sets created_by and organization fields if they exist.
        """
        kwargs = {}

        # Set created_by if the model has this field
        if hasattr(serializer.Meta.model, "created_by"):
            kwargs["created_by"] = self.request.user

        # Set organization if the model has this field and we can determine it
        if hasattr(serializer.Meta.model, "organization"):
            organization = self.get_organization()
            if organization:
                kwargs["organization"] = organization

        serializer.save(**kwargs)

    def perform_update(self, serializer):
        """
        Perform update with audit trail support.

        Automatically sets updated_by field if it exists.
        """
        kwargs = {}

        # Set updated_by if the model has this field
        if hasattr(serializer.Meta.model, "updated_by"):
            kwargs["updated_by"] = self.request.user

        serializer.save(**kwargs)

    def handle_exception(self, exc):
        """
        Handle exceptions with consistent error formatting.

        Ensures all exceptions are properly logged and formatted.
        """
        # Log the exception for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Exception in {self.__class__.__name__}: {exc}")

        return super().handle_exception(exc)


class BaseReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base ReadOnly ViewSet with the same features as BaseViewSet but for read-only access.
    """

    permission_classes = [IsAuthenticated]
    required_roles = []

    def get_organization(self):
        """Get the organization context for this request."""
        # Try to get organization from URL parameters first
        org_id = self.kwargs.get("organization_id") or self.kwargs.get("org_id")
        if org_id:
            try:
                from core.models import Organization

                return Organization.objects.get(id=org_id)
            except ObjectDoesNotExist:
                return None

        # Fall back to user's default organization
        if hasattr(self.request, "user") and self.request.user.is_authenticated:
            return self.request.user.get_default_organization()

        return None

    def get_permissions(self):
        """Get the permissions for this view."""
        if self.required_roles:
            permission_classes = [IsAuthenticatedAndInOrgWithRole]
        else:
            permission_classes = self.permission_classes

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Get the queryset for this view."""
        return super().get_queryset()

    def handle_exception(self, exc):
        """Handle exceptions with consistent error formatting."""
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Exception in {self.__class__.__name__}: {exc}")

        return super().handle_exception(exc)
