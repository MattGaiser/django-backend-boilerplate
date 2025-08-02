"""
Tests for experimental feature flag functionality.

This module tests the feature flag system that controls access to experimental
features at both organization and superuser levels.
"""

import pytest
from django.test import TestCase
from core.models import User, Organization, OrganizationMembership
from core.utils import is_experimental_enabled
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole


@pytest.mark.django_db
class TestExperimentalFeatureFlags(TestCase):
    """Test cases for the experimental feature flag system."""
    
    def setUp(self):
        """Set up test data."""
        # Create organizations
        self.org_experimental_true = OrganizationFactory.create(
            name="Experimental Org",
            is_experimental=True
        )
        self.org_experimental_false = OrganizationFactory.create(
            name="Non-Experimental Org", 
            is_experimental=False
        )
        
        # Create regular user
        self.regular_user = UserFactory.create(
            email="regular@example.com",
            is_superuser=False,
            is_experimental_user_override=False
        )
        
        # Create superuser with override disabled
        self.superuser_no_override = UserFactory.create(
            email="super1@example.com",
            is_superuser=True,
            is_experimental_user_override=False
        )
        
        # Create superuser with override enabled
        self.superuser_with_override = UserFactory.create(
            email="super2@example.com",
            is_superuser=True,
            is_experimental_user_override=True
        )
        
        # Create user with no organization
        self.user_no_org = UserFactory.create(
            email="noorg@example.com",
            is_superuser=False,
            is_experimental_user_override=False
        )
    
    def test_organization_experimental_flag_true(self):
        """Test that org-level experimental flag returns True when enabled."""
        # Create membership with experimental org
        OrganizationMembershipFactory.create(
            user=self.regular_user,
            organization=self.org_experimental_true,
            is_default=True,
            role=OrgRole.VIEWER
        )
        
        # Test using utility function
        self.assertTrue(is_experimental_enabled(self.regular_user))
        
        # Test using user method
        self.assertTrue(self.regular_user.is_experimental_enabled())
    
    def test_organization_experimental_flag_false(self):
        """Test that org-level experimental flag returns False when disabled."""
        # Create membership with non-experimental org
        OrganizationMembershipFactory.create(
            user=self.regular_user,
            organization=self.org_experimental_false,
            is_default=True,
            role=OrgRole.VIEWER
        )
        
        # Test using utility function
        self.assertFalse(is_experimental_enabled(self.regular_user))
        
        # Test using user method  
        self.assertFalse(self.regular_user.is_experimental_enabled())
    
    def test_superuser_override_enabled(self):
        """Test that superuser with override enabled returns True regardless of org flag."""
        # Test with experimental org
        OrganizationMembershipFactory.create(
            user=self.superuser_with_override,
            organization=self.org_experimental_true,
            is_default=True,
            role=OrgRole.ADMIN
        )
        
        self.assertTrue(is_experimental_enabled(self.superuser_with_override))
        self.assertTrue(self.superuser_with_override.is_experimental_enabled())
        
        # Clear existing membership and test with non-experimental org
        self.superuser_with_override.organization_memberships.all().delete()
        OrganizationMembershipFactory.create(
            user=self.superuser_with_override,
            organization=self.org_experimental_false,
            is_default=True,
            role=OrgRole.ADMIN
        )
        
        # Should still return True due to override
        self.assertTrue(is_experimental_enabled(self.superuser_with_override))
        self.assertTrue(self.superuser_with_override.is_experimental_enabled())
    
    def test_superuser_override_disabled(self):
        """Test that superuser with override disabled follows org flag."""
        # Test with experimental org - should return True based on org
        OrganizationMembershipFactory.create(
            user=self.superuser_no_override,
            organization=self.org_experimental_true,
            is_default=True,
            role=OrgRole.ADMIN
        )
        
        self.assertTrue(is_experimental_enabled(self.superuser_no_override))
        self.assertTrue(self.superuser_no_override.is_experimental_enabled())
        
        # Clear existing membership and test with non-experimental org
        self.superuser_no_override.organization_memberships.all().delete()
        OrganizationMembershipFactory.create(
            user=self.superuser_no_override,
            organization=self.org_experimental_false,
            is_default=True,
            role=OrgRole.ADMIN
        )
        
        # Should return False based on org
        self.assertFalse(is_experimental_enabled(self.superuser_no_override))
        self.assertFalse(self.superuser_no_override.is_experimental_enabled())
    
    def test_non_superuser_override_ignored(self):
        """Test that non-superuser users ignore the override field."""
        # Set override flag on regular user (should be ignored)
        self.regular_user.is_experimental_user_override = True
        self.regular_user.save()
        
        # Test with experimental org - should return True based on org, not override
        OrganizationMembershipFactory.create(
            user=self.regular_user,
            organization=self.org_experimental_true,
            is_default=True,
            role=OrgRole.VIEWER
        )
        
        self.assertTrue(is_experimental_enabled(self.regular_user))
        self.assertTrue(self.regular_user.is_experimental_enabled())
        
        # Clear existing membership and test with non-experimental org
        self.regular_user.organization_memberships.all().delete()
        OrganizationMembershipFactory.create(
            user=self.regular_user,
            organization=self.org_experimental_false,
            is_default=True,
            role=OrgRole.VIEWER
        )
        
        # Should return False based on org
        self.assertFalse(is_experimental_enabled(self.regular_user))
        self.assertFalse(self.regular_user.is_experimental_enabled())
    
    def test_user_with_no_organization(self):
        """Test that users with no default organization return False."""
        # Test regular user with no org
        self.assertFalse(is_experimental_enabled(self.user_no_org))
        self.assertFalse(self.user_no_org.is_experimental_enabled())
        
        # Test superuser with override but no org - should still return True
        superuser_no_org = UserFactory.create(
            email="supernoorg@example.com",
            is_superuser=True,
            is_experimental_user_override=True
        )
        
        self.assertTrue(is_experimental_enabled(superuser_no_org))
        self.assertTrue(superuser_no_org.is_experimental_enabled())
        
        # Test superuser without override and no org - should return False
        superuser_no_override_no_org = UserFactory.create(
            email="supernooverride@example.com",
            is_superuser=True,
            is_experimental_user_override=False
        )
        
        self.assertFalse(is_experimental_enabled(superuser_no_override_no_org))
        self.assertFalse(superuser_no_override_no_org.is_experimental_enabled())
    
    def test_model_field_defaults(self):
        """Test that model fields have correct default values."""
        # Test Organization default
        org = OrganizationFactory.create()
        self.assertFalse(org.is_experimental)
        
        # Test User default
        user = UserFactory.create()
        self.assertFalse(user.is_experimental_user_override)
    
    def test_field_help_text(self):
        """Test that model fields have appropriate help text."""
        # Get field instances
        org_field = Organization._meta.get_field('is_experimental')
        user_field = User._meta.get_field('is_experimental_user_override')
        
        # Check help text is present and meaningful
        self.assertIn('experimental', org_field.help_text.lower())
        self.assertIn('experimental', user_field.help_text.lower())
        self.assertIn('superuser', user_field.help_text.lower())


@pytest.mark.django_db
class TestExperimentalFeatureFlagsEdgeCases(TestCase):
    """Test edge cases for experimental feature flags."""
    
    def test_multiple_organizations(self):
        """Test user with multiple organizations uses default org."""
        user = UserFactory.create(is_superuser=False, is_experimental_user_override=False)
        
        # Create two orgs with different experimental settings
        org1 = OrganizationFactory.create(is_experimental=True)
        org2 = OrganizationFactory.create(is_experimental=False)
        
        # Make user member of both, but org2 is default
        OrganizationMembershipFactory.create(
            user=user, organization=org1, is_default=False, role=OrgRole.VIEWER
        )
        OrganizationMembershipFactory.create(
            user=user, organization=org2, is_default=True, role=OrgRole.VIEWER
        )
        
        # Should use default org (org2) which has experimental=False
        self.assertFalse(is_experimental_enabled(user))
        self.assertFalse(user.is_experimental_enabled())
    
    def test_superuser_override_priority(self):
        """Test that superuser override has priority over org settings."""
        superuser = UserFactory.create(
            is_superuser=True,
            is_experimental_user_override=True
        )
        
        # Create non-experimental org
        org = OrganizationFactory.create(is_experimental=False)
        OrganizationMembershipFactory.create(
            user=superuser, organization=org, is_default=True, role=OrgRole.ADMIN
        )
        
        # Should return True due to superuser override, despite org being False
        self.assertTrue(is_experimental_enabled(superuser))
        self.assertTrue(superuser.is_experimental_enabled())