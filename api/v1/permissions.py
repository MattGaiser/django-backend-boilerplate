"""
API v1 specific permission classes.

These permissions complement the common organization-scoped permissions
with API-specific requirements.
"""

from rest_framework.permissions import BasePermission
from django.utils.translation import gettext_lazy as _
from common.permissions.org_scoped import IsAuthenticatedAndInOrgWithRole
from constants.roles import OrgRole


class IsAuthenticatedAndInOrgWithRole(IsAuthenticatedAndInOrgWithRole):
    """
    API v1 specific version of the organization permission class.
    
    Extends the base permission with API-specific message handling.
    """
    
    message = _("You do not have permission to perform this action in this organization.")


class IsOwnerOrAdmin(BasePermission):
    """
    Permission that allows users to access their own resources or organization admins.
    
    Useful for endpoints where users should be able to access their own data,
    but organization admins should be able to access any user's data within the org.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user can access this specific object.
        """
        # Allow if the user is the owner of the object
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        # For User objects, check if it's the same user
        from core.models import User
        if isinstance(obj, User) and obj == request.user:
            return True
        
        # Allow if user is an admin in the relevant organization
        if hasattr(obj, 'organization'):
            user_role = request.user.get_role(obj.organization)
            return user_role == OrgRole.ADMIN
        
        return False


class CanViewUserData(BasePermission):
    """
    Permission for viewing user data within organization context.
    
    Allows:
    - Users to view their own data
    - Organization super admins, admins and managers to view data of users in their org
    """
    
    def has_permission(self, request, view):
        """Check basic permission for the view."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check permission for a specific user object."""
        from core.models import User
        
        # If it's not a User object, delegate to other permission classes
        if not isinstance(obj, User):
            return True
        
        # Users can always view their own data
        if obj == request.user:
            return True
        
        # Check if the requesting user has super admin, admin or manager role in any shared organization
        requesting_user_orgs = set(request.user.organizations.all())
        target_user_orgs = set(obj.organizations.all())
        shared_orgs = requesting_user_orgs.intersection(target_user_orgs)
        
        for org in shared_orgs:
            user_role = request.user.get_role(org)
            if user_role in [OrgRole.SUPER_ADMIN, OrgRole.ADMIN, OrgRole.MANAGER]:
                return True
        
        return False