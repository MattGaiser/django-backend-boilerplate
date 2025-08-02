"""
Organization-scoped permissions for multi-tenant RBAC support.

These permission classes ensure that users can only access resources
within organizations they are members of, with appropriate role-based access control.
"""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from constants.roles import OrgRole


class IsAuthenticatedAndInOrgWithRole(BasePermission):
    """
    Permission class that enforces authentication and organization membership with specific roles.
    
    Requires the view to have a `required_roles` attribute specifying the allowed roles.
    The view must also implement `get_organization()` method to determine the target organization.
    
    Usage:
        class MyViewSet(BaseViewSet):
            required_roles = [OrgRole.ADMIN, OrgRole.MANAGER]
            
            def get_organization(self):
                # Return the organization for this request
                return self.get_object().organization
    """
    
    def has_permission(self, request, view):
        """
        Check if the user is authenticated and has the required role in the organization.
        
        Args:
            request: HTTP request object
            view: DRF view instance
            
        Returns:
            bool: True if permission is granted, False otherwise
        """
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if view has required_roles defined
        required_roles = getattr(view, 'required_roles', None)
        if required_roles is None:
            # If no roles are specified, default to allowing authenticated users
            return True
        
        # If required_roles is an empty list, still allow authenticated users
        if isinstance(required_roles, list) and len(required_roles) == 0:
            return True
        
        # Get the organization for this request
        try:
            organization = view.get_organization()
        except AttributeError:
            raise PermissionDenied(
                _("View must implement get_organization() method when using role-based permissions.")
            )
        except Exception:
            # If we can't determine the organization, deny access
            return False
        
        if not organization:
            return False
        
        # Check if user has the required role in this organization
        user_role = request.user.get_role(organization)
        
        if user_role not in required_roles:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access a specific object.
        
        This ensures that the object belongs to an organization the user has access to.
        """
        # First check the basic permission
        if not self.has_permission(request, view):
            return False
        
        # If the object has an organization attribute, check if user has access
        if hasattr(obj, 'organization'):
            user_role = request.user.get_role(obj.organization)
            required_roles = getattr(view, 'required_roles', [])
            return user_role in required_roles
        
        # If no organization attribute, default to allowing access
        # (the object-level check should be handled by other means)
        return True


class IsOrgAdmin(IsAuthenticatedAndInOrgWithRole):
    """
    Convenience permission class that requires ADMIN role in the organization.
    """
    
    def has_permission(self, request, view):
        # Set required_roles to ADMIN only
        view.required_roles = [OrgRole.ADMIN]
        return super().has_permission(request, view)


class IsOrgAdminOrManager(IsAuthenticatedAndInOrgWithRole):
    """
    Convenience permission class that requires ADMIN or MANAGER role in the organization.
    """
    
    def has_permission(self, request, view):
        # Set required_roles to ADMIN and MANAGER
        view.required_roles = [OrgRole.ADMIN, OrgRole.MANAGER]
        return super().has_permission(request, view)


class IsOrgMember(IsAuthenticatedAndInOrgWithRole):
    """
    Convenience permission class that allows any member of the organization.
    """
    
    def has_permission(self, request, view):
        # Set required_roles to all available roles
        view.required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.VIEWER]
        return super().has_permission(request, view)