"""
Tests for API v1 permission classes.

Tests organization-scoped permissions and role-based access control.
"""

import pytest
from django.test import TestCase
from unittest.mock import Mock
from rest_framework.exceptions import PermissionDenied
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from common.permissions.org_scoped import (
    IsAuthenticatedAndInOrgWithRole,
    IsOrgAdmin,
    IsOrgAdminOrManager,
    IsOrgMember
)
from api.v1.permissions import IsOwnerOrAdmin, CanViewUserData
from constants.roles import OrgRole


class IsAuthenticatedAndInOrgWithRoleTestCase(TestCase):
    """
    Test cases for the base organization permission class.
    """
    
    def setUp(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.admin_user = UserFactory()
        self.manager_user = UserFactory()
        self.viewer_user = UserFactory()
        self.non_member_user = UserFactory()
        
        # Create memberships
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        OrganizationMembershipFactory(
            user=self.manager_user,
            organization=self.organization,
            role=OrgRole.MANAGER
        )
        OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        
        self.permission = IsAuthenticatedAndInOrgWithRole()
    
    def _create_mock_request(self, user):
        """Create a mock request with the given user."""
        request = Mock()
        request.user = user
        return request
    
    def _create_mock_view(self, required_roles, organization=None):
        """Create a mock view with required roles and organization."""
        view = Mock()
        view.required_roles = required_roles
        if organization:
            view.get_organization.return_value = organization
        else:
            view.get_organization.return_value = self.organization
        return view
    
    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied."""
        request = self._create_mock_request(None)
        view = self._create_mock_view([OrgRole.ADMIN])
        
        result = self.permission.has_permission(request, view)
        self.assertFalse(result)
    
    def test_no_required_roles_allows_authenticated_user(self):
        """Test that authenticated users are allowed when no roles are required."""
        request = self._create_mock_request(self.viewer_user)
        view = self._create_mock_view([])  # No required roles
        
        result = self.permission.has_permission(request, view)
        self.assertTrue(result)
    
    def test_admin_user_with_admin_role_allowed(self):
        """Test that admin user is allowed when admin role is required."""
        request = self._create_mock_request(self.admin_user)
        view = self._create_mock_view([OrgRole.ADMIN])
        
        result = self.permission.has_permission(request, view)
        self.assertTrue(result)
    
    def test_manager_user_with_admin_role_denied(self):
        """Test that manager user is denied when admin role is required."""
        request = self._create_mock_request(self.manager_user)
        view = self._create_mock_view([OrgRole.ADMIN])
        
        result = self.permission.has_permission(request, view)
        self.assertFalse(result)
    
    def test_manager_user_with_manager_role_allowed(self):
        """Test that manager user is allowed when manager role is required."""
        request = self._create_mock_request(self.manager_user)
        view = self._create_mock_view([OrgRole.MANAGER, OrgRole.ADMIN])
        
        result = self.permission.has_permission(request, view)
        self.assertTrue(result)
    
    def test_non_member_user_denied(self):
        """Test that non-organization members are denied."""
        request = self._create_mock_request(self.non_member_user)
        view = self._create_mock_view([OrgRole.VIEWER])
        
        result = self.permission.has_permission(request, view)
        self.assertFalse(result)
    
    def test_view_without_get_organization_raises_error(self):
        """Test that views without get_organization method raise an error."""
        request = self._create_mock_request(self.admin_user)
        view = Mock()
        view.required_roles = [OrgRole.ADMIN]
        del view.get_organization  # Remove the method
        
        with self.assertRaises(PermissionDenied):
            self.permission.has_permission(request, view)
    
    def test_object_permission_with_organization(self):
        """Test object-level permission for objects with organization."""
        request = self._create_mock_request(self.admin_user)
        view = self._create_mock_view([OrgRole.ADMIN])
        
        # Mock object with organization
        obj = Mock()
        obj.organization = self.organization
        
        result = self.permission.has_object_permission(request, view, obj)
        self.assertTrue(result)


class ConveniencePermissionTestCase(TestCase):
    """
    Test cases for convenience permission classes.
    """
    
    def setUp(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.admin_user = UserFactory()
        self.manager_user = UserFactory()
        
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        OrganizationMembershipFactory(
            user=self.manager_user,
            organization=self.organization,
            role=OrgRole.MANAGER
        )
    
    def _create_mock_request(self, user):
        """Create a mock request with the given user."""
        request = Mock()
        request.user = user
        return request
    
    def _create_mock_view(self, organization=None):
        """Create a mock view with organization."""
        view = Mock()
        if organization:
            view.get_organization.return_value = organization
        else:
            view.get_organization.return_value = self.organization
        return view
    
    def test_is_org_admin_permission(self):
        """Test IsOrgAdmin convenience permission."""
        permission = IsOrgAdmin()
        
        # Admin user should be allowed
        request = self._create_mock_request(self.admin_user)
        view = self._create_mock_view()
        result = permission.has_permission(request, view)
        self.assertTrue(result)
        
        # Manager user should be denied
        request = self._create_mock_request(self.manager_user)
        view = self._create_mock_view()
        result = permission.has_permission(request, view)
        self.assertFalse(result)
    
    def test_is_org_admin_or_manager_permission(self):
        """Test IsOrgAdminOrManager convenience permission."""
        permission = IsOrgAdminOrManager()
        
        # Admin user should be allowed
        request = self._create_mock_request(self.admin_user)
        view = self._create_mock_view()
        result = permission.has_permission(request, view)
        self.assertTrue(result)
        
        # Manager user should be allowed
        request = self._create_mock_request(self.manager_user)
        view = self._create_mock_view()
        result = permission.has_permission(request, view)
        self.assertTrue(result)
    
    def test_is_org_member_permission(self):
        """Test IsOrgMember convenience permission."""
        permission = IsOrgMember()
        
        # Both admin and manager should be allowed
        for user in [self.admin_user, self.manager_user]:
            request = self._create_mock_request(user)
            view = self._create_mock_view()
            result = permission.has_permission(request, view)
            self.assertTrue(result)


class APISpecificPermissionTestCase(TestCase):
    """
    Test cases for API-specific permission classes.
    """
    
    def setUp(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.admin_user = UserFactory()
        
        OrganizationMembershipFactory(
            user=self.user1,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        OrganizationMembershipFactory(
            user=self.user2,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
    
    def test_is_owner_or_admin_user_can_access_own_data(self):
        """Test that users can access their own data."""
        permission = IsOwnerOrAdmin()
        request = Mock()
        request.user = self.user1
        view = Mock()
        
        result = permission.has_object_permission(request, view, self.user1)
        self.assertTrue(result)
    
    def test_is_owner_or_admin_user_cannot_access_other_user_data(self):
        """Test that regular users cannot access other users' data."""
        permission = IsOwnerOrAdmin()
        request = Mock()
        request.user = self.user1
        view = Mock()
        
        result = permission.has_object_permission(request, view, self.user2)
        self.assertFalse(result)
    
    def test_is_owner_or_admin_admin_can_access_any_user_data(self):
        """Test that admins can access any user's data in their org."""
        permission = IsOwnerOrAdmin()
        request = Mock()
        request.user = self.admin_user
        view = Mock()
        
        # Mock user2 with organization
        self.user2.organization = self.organization
        
        result = permission.has_object_permission(request, view, self.user2)
        self.assertTrue(result)
    
    def test_can_view_user_data_same_org_members(self):
        """Test that users can view data of members in same organization."""
        permission = CanViewUserData()
        request = Mock()
        request.user = self.admin_user
        view = Mock()
        
        result = permission.has_object_permission(request, view, self.user1)
        self.assertTrue(result)
    
    def test_can_view_user_data_own_data(self):
        """Test that users can view their own data."""
        permission = CanViewUserData()
        request = Mock()
        request.user = self.user1
        view = Mock()
        
        result = permission.has_object_permission(request, view, self.user1)
        self.assertTrue(result)