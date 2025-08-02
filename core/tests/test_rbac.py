from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.views.generic import View
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import path
from django.conf import settings
from django.test.utils import override_settings

from core.models import Organization, OrganizationMembership
from core.mixins import OrgScopedPermissionMixin
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole


User = get_user_model()


# Test view for HTTP response testing
class RBACTestView(OrgScopedPermissionMixin, View):
    required_role = OrgRole.ADMIN
    
    def get(self, request, *args, **kwargs):
        return HttpResponse("Access granted")


# URL patterns for testing
test_urlpatterns = [
    path('org/<uuid:org_id>/admin-view/', RBACTestView.as_view(), name='test-rbac-view'),
]


class TestUserHasRole(TestCase):
    """Test cases for the User.has_role() method."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.org = OrganizationFactory()
        
    def test_has_role_with_correct_role(self):
        """Test has_role returns True when user has the specified role."""
        # Create membership with admin role
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        
        self.assertTrue(self.user.has_role(self.org, OrgRole.ADMIN))
        
    def test_has_role_with_different_role(self):
        """Test has_role returns False when user has a different role."""
        # Create membership with viewer role
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.VIEWER
        )
        
        self.assertFalse(self.user.has_role(self.org, OrgRole.ADMIN))
        self.assertTrue(self.user.has_role(self.org, OrgRole.VIEWER))
        
    def test_has_role_no_membership(self):
        """Test has_role returns False when user has no membership in organization."""
        self.assertFalse(self.user.has_role(self.org, OrgRole.ADMIN))
        
    def test_has_role_multiple_organizations(self):
        """Test has_role works correctly with multiple organizations."""
        org2 = OrganizationFactory()
        
        # Create memberships in different orgs with different roles
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        OrganizationMembershipFactory(
            user=self.user,
            organization=org2,
            role=OrgRole.VIEWER
        )
        
        self.assertTrue(self.user.has_role(self.org, OrgRole.ADMIN))
        self.assertFalse(self.user.has_role(self.org, OrgRole.VIEWER))
        self.assertTrue(self.user.has_role(org2, OrgRole.VIEWER))
        self.assertFalse(self.user.has_role(org2, OrgRole.ADMIN))
        
    def test_has_role_different_users_same_org(self):
        """Test has_role works correctly with different users in the same organization."""
        user2 = UserFactory()
        
        # Create different memberships for different users
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        OrganizationMembershipFactory(
            user=user2,
            organization=self.org,
            role=OrgRole.MANAGER
        )
        
        self.assertTrue(self.user.has_role(self.org, OrgRole.ADMIN))
        self.assertFalse(self.user.has_role(self.org, OrgRole.MANAGER))
        self.assertTrue(user2.has_role(self.org, OrgRole.MANAGER))
        self.assertFalse(user2.has_role(self.org, OrgRole.ADMIN))


class TestOrgScopedPermissionMixin(TestCase):
    """Test cases for the OrgScopedPermissionMixin."""

    def setUp(self):
        """Set up test data and mock view."""
        self.factory = RequestFactory()
        self.user = UserFactory()
        self.org = OrganizationFactory()
        
        # Create a test view class
        class TestView(OrgScopedPermissionMixin, View):
            required_role = OrgRole.ADMIN
            
            def get(self, request, *args, **kwargs):
                return HttpResponse("Success")
        
        self.view_class = TestView
        
    def test_authenticated_user_with_correct_role(self):
        """Test that authenticated user with correct role can access the view."""
        # Create admin membership
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = self.user
        
        view = self.view_class()
        view.setup(request, org_id=self.org.id)
        
        response = view.dispatch(request, org_id=self.org.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
        
    def test_authenticated_user_with_wrong_role(self):
        """Test that authenticated user with wrong role gets permission denied."""
        # Create viewer membership (not admin)
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.VIEWER
        )
        
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = self.user
        
        view = self.view_class()
        view.setup(request, org_id=self.org.id)
        
        with self.assertRaises(PermissionDenied) as cm:
            view.dispatch(request, org_id=self.org.id)
        
        self.assertIn("You do not have the required role", str(cm.exception))
        
    def test_unauthenticated_user(self):
        """Test that unauthenticated user gets redirected to login."""
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = AnonymousUser()
        
        view = self.view_class()
        view.setup(request, org_id=self.org.id)
        
        response = view.dispatch(request, org_id=self.org.id)
        # LoginRequiredMixin should redirect to login
        self.assertEqual(response.status_code, 302)
        
    def test_nonexistent_organization(self):
        """Test that nonexistent organization raises Http404."""
        fake_org_id = '00000000-0000-0000-0000-000000000000'
        request = self.factory.get(f'/test/{fake_org_id}/')
        request.user = self.user
        
        view = self.view_class()
        view.setup(request, org_id=fake_org_id)
        
        with self.assertRaises(Http404):
            view.dispatch(request, org_id=fake_org_id)
            
    def test_user_not_member_of_organization(self):
        """Test that user who is not a member of the organization gets permission denied."""
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = self.user
        
        view = self.view_class()
        view.setup(request, org_id=self.org.id)
        
        with self.assertRaises(PermissionDenied):
            view.dispatch(request, org_id=self.org.id)
            
    def test_multiple_required_roles(self):
        """Test view with multiple acceptable roles."""
        class MultiRoleView(OrgScopedPermissionMixin, View):
            required_role = [OrgRole.ADMIN, OrgRole.MANAGER]
            
            def get(self, request, *args, **kwargs):
                return HttpResponse("Success")
        
        # Test with admin role
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = self.user
        
        view = MultiRoleView()
        view.setup(request, org_id=self.org.id)
        
        response = view.dispatch(request, org_id=self.org.id)
        self.assertEqual(response.status_code, 200)
        
        # Test with manager role
        self.user.organization_memberships.all().delete()
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.MANAGER
        )
        
        response = view.dispatch(request, org_id=self.org.id)
        self.assertEqual(response.status_code, 200)
        
        # Test with viewer role (should fail)
        self.user.organization_memberships.all().delete()
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.VIEWER
        )
        
        with self.assertRaises(PermissionDenied):
            view.dispatch(request, org_id=self.org.id)
            
    def test_custom_org_lookup_field(self):
        """Test view with custom organization lookup field."""
        class CustomLookupView(OrgScopedPermissionMixin, View):
            required_role = OrgRole.ADMIN
            org_lookup_field = 'organization_id'
            
            def get(self, request, *args, **kwargs):
                return HttpResponse("Success")
        
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = self.user
        
        view = CustomLookupView()
        view.setup(request, organization_id=self.org.id)
        
        response = view.dispatch(request, organization_id=self.org.id)
        self.assertEqual(response.status_code, 200)
        
    def test_view_stores_organization(self):
        """Test that the view stores the organization for use in other methods."""
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = self.user
        
        view = self.view_class()
        view.setup(request, org_id=self.org.id)
        view.dispatch(request, org_id=self.org.id)
        
        # Check that organization is stored in the view
        self.assertEqual(view.organization, self.org)
        
    def test_raise_404_on_no_org_false(self):
        """Test that setting raise_404_on_no_org=False raises PermissionDenied instead."""
        class PermissionDeniedView(OrgScopedPermissionMixin, View):
            required_role = OrgRole.ADMIN
            raise_404_on_no_org = False
            
            def get(self, request, *args, **kwargs):
                return HttpResponse("Success")
        
        fake_org_id = '00000000-0000-0000-0000-000000000000'
        request = self.factory.get(f'/test/{fake_org_id}/')
        request.user = self.user
        
        view = PermissionDeniedView()
        view.setup(request, org_id=fake_org_id)
        
        with self.assertRaises(PermissionDenied) as cm:
            view.dispatch(request, org_id=fake_org_id)
        
        self.assertIn("Organization not found", str(cm.exception))
        
    def test_no_required_role_raises_error(self):
        """Test that view without required_role raises NotImplementedError."""
        class NoRoleView(OrgScopedPermissionMixin, View):
            # No required_role defined
            
            def get(self, request, *args, **kwargs):
                return HttpResponse("Success")
        
        request = self.factory.get(f'/test/{self.org.id}/')
        request.user = self.user
        
        view = NoRoleView()
        view.setup(request, org_id=self.org.id)
        
        with self.assertRaises(NotImplementedError) as cm:
            view.dispatch(request, org_id=self.org.id)
        
        self.assertIn("requires 'required_role' to be defined", str(cm.exception))


@override_settings(ROOT_URLCONF='core.tests.test_rbac')
class TestRBACHTTPResponses(TestCase):
    """Test HTTP responses for RBAC scenarios."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.org = OrganizationFactory()
        
    def test_403_response_on_permission_denied(self):
        """Test that views return 403 when user lacks required role."""
        # Create user with viewer role (not admin)
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.VIEWER
        )
        
        # Login the user
        self.client.force_login(self.user)
        
        # Access the admin-only view
        response = self.client.get(f'/org/{self.org.id}/admin-view/')
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
    def test_403_response_on_no_membership(self):
        """Test that views return 403 when user is not a member of the organization."""
        # Login user but don't create any organization membership
        self.client.force_login(self.user)
        
        response = self.client.get(f'/org/{self.org.id}/admin-view/')
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
    def test_404_response_on_nonexistent_org(self):
        """Test that views return 404 when organization doesn't exist."""
        self.client.force_login(self.user)
        
        fake_org_id = '00000000-0000-0000-0000-000000000000'
        response = self.client.get(f'/org/{fake_org_id}/admin-view/')
        
        # Should get 404 Not Found
        self.assertEqual(response.status_code, 404)
        
    def test_success_response_with_correct_role(self):
        """Test that views return 200 when user has the required role."""
        # Create user with admin role
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN
        )
        
        self.client.force_login(self.user)
        
        response = self.client.get(f'/org/{self.org.id}/admin-view/')
        
        # Should get 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Access granted")


# URL configuration for testing
urlpatterns = test_urlpatterns