from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404


class OrgScopedPermissionMixin(LoginRequiredMixin):
    """
    Mixin for class-based views that enforces organization-scoped role-based access control.

    This mixin requires the user to be authenticated and have a specific role within
    the organization context. It should be used with views that operate within
    an organization scope.

    Attributes:
        required_role (str or list): The role(s) required to access this view.
                                   Can be a single role string or a list of acceptable roles.
        org_lookup_field (str): The URL parameter or attribute name used to identify the organization.
                               Defaults to 'org_id' for URL parameters.
        raise_404_on_no_org (bool): Whether to raise Http404 when organization is not found.
                                   Defaults to True.

    Raises:
        PermissionDenied: When user doesn't have required role in the organization.
        Http404: When organization is not found and raise_404_on_no_org is True.
    """

    required_role = None
    org_lookup_field = "org_id"
    raise_404_on_no_org = True

    def get_organization(self):
        """
        Get the organization for the current request.

        This method can be overridden to customize how the organization is determined.
        By default, it looks for the organization ID in URL parameters.

        Returns:
            Organization instance or None if not found
        """
        from core.models import Organization

        org_id = self.kwargs.get(self.org_lookup_field)
        if not org_id:
            return None

        try:
            return Organization.objects.get(id=org_id, is_active=True)
        except Organization.DoesNotExist:
            return None

    def get_required_roles(self):
        """
        Get the list of required roles for this view.

        Returns:
            list: List of role strings that are acceptable for this view
        """
        if self.required_role is None:
            raise NotImplementedError(
                "OrgScopedPermissionMixin requires 'required_role' to be defined"
            )

        if isinstance(self.required_role, str):
            return [self.required_role]
        elif isinstance(self.required_role, (list, tuple)):
            return list(self.required_role)
        else:
            raise ValueError("required_role must be a string or list of strings")

    def has_permission(self, user, organization):
        """
        Check if the user has permission to access this view.

        Args:
            user: The authenticated user
            organization: The organization instance

        Returns:
            bool: True if user has required permission, False otherwise
        """
        if not organization:
            return False

        required_roles = self.get_required_roles()
        user_role = user.get_role(organization)

        return user_role in required_roles

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to enforce role-based permissions before processing the request.
        """
        # First check if user is authenticated (handled by LoginRequiredMixin)
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Get the organization for this request
        organization = self.get_organization()

        if not organization:
            if self.raise_404_on_no_org:
                raise Http404("Organization not found")
            else:
                raise PermissionDenied("Organization not found")

        # Check if user has required role in this organization
        if not self.has_permission(request.user, organization):
            raise PermissionDenied(
                f"You do not have the required role ({', '.join(self.get_required_roles())}) "
                f"in this organization"
            )

        # Store organization in the view for use in other methods
        self.organization = organization

        return super().dispatch(request, *args, **kwargs)
