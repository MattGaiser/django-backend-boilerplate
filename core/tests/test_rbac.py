"""
RBAC (Role-Based Access Control) tests for membership-based role enforcement.

These tests validate organization-based access control using the OrgRole system
and OrganizationMembership model, including an example view for testing.
"""

from django.test import TestCase, RequestFactory
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import get_user_model

from core.models import Organization, OrganizationMembership, OrgRole
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory

User = get_user_model()


# Example view classes for testing RBAC
class OrganizationRequiredMixin:
    """
    Mixin that requires the user to be a member of an organization.
    This is an example implementation for testing RBAC logic.
    """
    
    required_role = OrgRole.VIEWER  # Default minimum role
    
    def get_organization(self, request):
        """Get the organization from the request. Override in subclasses."""
        # For testing, we'll pass it as a parameter
        return getattr(request, 'test_organization', None)
    
    def check_organization_access(self, request, organization):
        """Check if user has required access to the organization."""
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required")
        
        if not organization:
            raise PermissionDenied("Organization not found")
        
        # Get user's role in the organization
        user_role = request.user.get_role(organization)
        if not user_role:
            raise PermissionDenied("User is not a member of this organization")
        
        # Check if user's role meets the minimum requirement
        role_hierarchy = {
            OrgRole.VIEWER: 1,
            OrgRole.EDITOR: 2,
            OrgRole.ADMIN: 3,
            OrgRole.SUPER_ADMIN: 4,
        }
        
        required_level = role_hierarchy.get(self.required_role, 1)
        user_level = role_hierarchy.get(user_role, 0)
        
        if user_level < required_level:
            raise PermissionDenied(
                f"Insufficient permissions. Required: {self.required_role}, "
                f"User has: {user_role}"
            )
        
        return True


class ExampleOrganizationView(OrganizationRequiredMixin, View):
    """Example view that requires organization membership for testing."""
    
    def get(self, request):
        organization = self.get_organization(request)
        self.check_organization_access(request, organization)
        
        return JsonResponse({
            'organization': organization.name,
            'user': request.user.email,
            'role': request.user.get_role(organization),
            'message': 'Access granted'
        })


class ExampleAdminView(OrganizationRequiredMixin, View):
    """Example view that requires admin role for testing."""
    
    required_role = OrgRole.ADMIN
    
    def get(self, request):
        organization = self.get_organization(request)
        self.check_organization_access(request, organization)
        
        return JsonResponse({
            'organization': organization.name,
            'user': request.user.email,
            'role': request.user.get_role(organization),
            'message': 'Admin access granted'
        })


class ExampleSuperAdminView(OrganizationRequiredMixin, View):
    """Example view that requires super admin role for testing."""
    
    required_role = OrgRole.SUPER_ADMIN
    
    def get(self, request):
        organization = self.get_organization(request)
        self.check_organization_access(request, organization)
        
        return JsonResponse({
            'organization': organization.name,
            'user': request.user.email,
            'role': request.user.get_role(organization),
            'message': 'Super admin access granted'
        })


class TestRBACMembershipBasedAccess(TestCase):
    """Test role-based access control using organization memberships."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.organization = OrganizationFactory(name="Test Organization")
        
        # Create users with different roles
        self.viewer_user = UserFactory()
        self.editor_user = UserFactory()
        self.admin_user = UserFactory()
        self.super_admin_user = UserFactory()
        self.non_member_user = UserFactory()
        
        # Create memberships with different roles
        OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        OrganizationMembershipFactory(
            user=self.editor_user,
            organization=self.organization,
            role=OrgRole.EDITOR
        )
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        OrganizationMembershipFactory(
            user=self.super_admin_user,
            organization=self.organization,
            role=OrgRole.SUPER_ADMIN
        )
        # non_member_user has no membership
    
    def test_viewer_role_access_to_basic_view(self):
        """Test that viewer role can access basic organization view."""
        request = self.factory.get('/test/')
        request.user = self.viewer_user
        request.test_organization = self.organization
        
        view = ExampleOrganizationView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['role'], OrgRole.VIEWER)
        self.assertEqual(data['message'], 'Access granted')
    
    def test_editor_role_access_to_basic_view(self):
        """Test that editor role can access basic organization view."""
        request = self.factory.get('/test/')
        request.user = self.editor_user
        request.test_organization = self.organization
        
        view = ExampleOrganizationView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.EDITOR)
        self.assertEqual(data['message'], 'Access granted')
    
    def test_admin_role_access_to_basic_view(self):
        """Test that admin role can access basic organization view."""
        request = self.factory.get('/test/')
        request.user = self.admin_user
        request.test_organization = self.organization
        
        view = ExampleOrganizationView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.ADMIN)
        self.assertEqual(data['message'], 'Access granted')
    
    def test_non_member_denied_access(self):
        """Test that non-members are denied access."""
        request = self.factory.get('/test/')
        request.user = self.non_member_user
        request.test_organization = self.organization
        
        view = ExampleOrganizationView()
        
        with self.assertRaises(PermissionDenied) as cm:
            view.get(request)
        
        self.assertIn("User is not a member of this organization", str(cm.exception))
    
    def test_unauthenticated_user_denied_access(self):
        """Test that unauthenticated users are denied access."""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request.test_organization = self.organization
        
        view = ExampleOrganizationView()
        
        with self.assertRaises(PermissionDenied) as cm:
            view.get(request)
        
        self.assertIn("Authentication required", str(cm.exception))


class TestRBACRoleHierarchy(TestCase):
    """Test role hierarchy enforcement in RBAC system."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.organization = OrganizationFactory(name="Test Organization")
        
        # Create users with different roles
        self.viewer_user = UserFactory()
        self.editor_user = UserFactory()
        self.admin_user = UserFactory()
        self.super_admin_user = UserFactory()
        
        # Create memberships
        OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        OrganizationMembershipFactory(
            user=self.editor_user,
            organization=self.organization,
            role=OrgRole.EDITOR
        )
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        OrganizationMembershipFactory(
            user=self.super_admin_user,
            organization=self.organization,
            role=OrgRole.SUPER_ADMIN
        )
    
    def test_viewer_denied_admin_access(self):
        """Test that viewer role is denied access to admin-only view."""
        request = self.factory.get('/admin/')
        request.user = self.viewer_user
        request.test_organization = self.organization
        
        view = ExampleAdminView()
        
        with self.assertRaises(PermissionDenied) as cm:
            view.get(request)
        
        self.assertIn("Insufficient permissions", str(cm.exception))
        self.assertIn("Required: admin", str(cm.exception))
        self.assertIn("User has: viewer", str(cm.exception))
    
    def test_editor_denied_admin_access(self):
        """Test that editor role is denied access to admin-only view."""
        request = self.factory.get('/admin/')
        request.user = self.editor_user
        request.test_organization = self.organization
        
        view = ExampleAdminView()
        
        with self.assertRaises(PermissionDenied) as cm:
            view.get(request)
        
        self.assertIn("Insufficient permissions", str(cm.exception))
        self.assertIn("Required: admin", str(cm.exception))
        self.assertIn("User has: editor", str(cm.exception))
    
    def test_admin_granted_admin_access(self):
        """Test that admin role is granted access to admin-only view."""
        request = self.factory.get('/admin/')
        request.user = self.admin_user
        request.test_organization = self.organization
        
        view = ExampleAdminView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.ADMIN)
        self.assertEqual(data['message'], 'Admin access granted')
    
    def test_super_admin_granted_admin_access(self):
        """Test that super admin role is granted access to admin-only view."""
        request = self.factory.get('/admin/')
        request.user = self.super_admin_user
        request.test_organization = self.organization
        
        view = ExampleAdminView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.SUPER_ADMIN)
        self.assertEqual(data['message'], 'Admin access granted')
    
    def test_admin_denied_super_admin_access(self):
        """Test that admin role is denied access to super admin-only view."""
        request = self.factory.get('/superadmin/')
        request.user = self.admin_user
        request.test_organization = self.organization
        
        view = ExampleSuperAdminView()
        
        with self.assertRaises(PermissionDenied) as cm:
            view.get(request)
        
        self.assertIn("Insufficient permissions", str(cm.exception))
        self.assertIn("Required: super_admin", str(cm.exception))
        self.assertIn("User has: admin", str(cm.exception))
    
    def test_super_admin_granted_super_admin_access(self):
        """Test that super admin role is granted access to super admin-only view."""
        request = self.factory.get('/superadmin/')
        request.user = self.super_admin_user
        request.test_organization = self.organization
        
        view = ExampleSuperAdminView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.SUPER_ADMIN)
        self.assertEqual(data['message'], 'Super admin access granted')


class TestRBACMultipleOrganizations(TestCase):
    """Test RBAC with users belonging to multiple organizations."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()
        
        # Create two organizations
        self.org1 = OrganizationFactory(name="Organization 1")
        self.org2 = OrganizationFactory(name="Organization 2")
        
        # User is admin in org1, viewer in org2
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org1,
            role=OrgRole.ADMIN
        )
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org2,
            role=OrgRole.VIEWER
        )
    
    def test_admin_access_in_first_organization(self):
        """Test user has admin access in organization where they are admin."""
        request = self.factory.get('/admin/')
        request.user = self.user
        request.test_organization = self.org1
        
        view = ExampleAdminView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.ADMIN)
        self.assertEqual(data['organization'], "Organization 1")
    
    def test_viewer_access_denied_admin_in_second_organization(self):
        """Test user is denied admin access in organization where they are viewer."""
        request = self.factory.get('/admin/')
        request.user = self.user
        request.test_organization = self.org2
        
        view = ExampleAdminView()
        
        with self.assertRaises(PermissionDenied) as cm:
            view.get(request)
        
        self.assertIn("Insufficient permissions", str(cm.exception))
        self.assertIn("Required: admin", str(cm.exception))
        self.assertIn("User has: viewer", str(cm.exception))
    
    def test_viewer_access_granted_in_second_organization(self):
        """Test user has viewer access in organization where they are viewer."""
        request = self.factory.get('/view/')
        request.user = self.user
        request.test_organization = self.org2
        
        view = ExampleOrganizationView()
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.VIEWER)
        self.assertEqual(data['organization'], "Organization 2")


class TestRBACEdgeCases(TestCase):
    """Test edge cases in RBAC implementation."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()
        self.organization = OrganizationFactory()
    
    def test_missing_organization_denied_access(self):
        """Test that missing organization results in access denial."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.test_organization = None
        
        view = ExampleOrganizationView()
        
        with self.assertRaises(PermissionDenied) as cm:
            view.get(request)
        
        self.assertIn("Organization not found", str(cm.exception))
    
    def test_user_role_methods(self):
        """Test User model's organization-related methods."""
        # Test with no membership
        self.assertIsNone(self.user.get_role(self.organization))
        self.assertIsNone(self.user.get_membership(self.organization))
        
        # Create membership
        membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.organization,
            role=OrgRole.EDITOR,
            is_default=True
        )
        
        # Test with membership
        self.assertEqual(self.user.get_role(self.organization), OrgRole.EDITOR)
        self.assertEqual(self.user.get_membership(self.organization), membership)
        self.assertEqual(self.user.get_default_organization(), self.organization)
    
    def test_organization_membership_role_inheritance(self):
        """Test that role changes are immediately reflected in access control."""
        # Create membership with viewer role
        membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        
        # Verify viewer access works
        request = self.factory.get('/view/')
        request.user = self.user
        request.test_organization = self.organization
        view = ExampleOrganizationView()
        response = view.get(request)
        self.assertEqual(response.status_code, 200)
        
        # Verify admin access fails
        admin_view = ExampleAdminView()
        with self.assertRaises(PermissionDenied):
            admin_view.get(request)
        
        # Upgrade to admin role
        membership.role = OrgRole.ADMIN
        membership.save()
        
        # Verify admin access now works
        response = admin_view.get(request)
        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data['role'], OrgRole.ADMIN)