import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from core.models import Organization, OrganizationMembership, OrgRole
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory

User = get_user_model()


class TestOrgRole(TestCase):
    """Test cases for the OrgRole enum."""
    
    def test_org_role_choices(self):
        """Test that OrgRole has the expected choices."""
        expected_choices = [
            ('super_admin', 'Super Admin'),
            ('admin', 'Admin'),
            ('editor', 'Editor'),
            ('viewer', 'Viewer'),
        ]
        self.assertEqual(OrgRole.choices, expected_choices)
    
    def test_org_role_values(self):
        """Test OrgRole enum values."""
        self.assertEqual(OrgRole.SUPER_ADMIN, 'super_admin')
        self.assertEqual(OrgRole.ADMIN, 'admin')
        self.assertEqual(OrgRole.EDITOR, 'editor')
        self.assertEqual(OrgRole.VIEWER, 'viewer')
    
    def test_org_role_labels(self):
        """Test OrgRole enum labels."""
        self.assertEqual(OrgRole.SUPER_ADMIN.label, 'Super Admin')
        self.assertEqual(OrgRole.ADMIN.label, 'Admin')
        self.assertEqual(OrgRole.EDITOR.label, 'Editor')
        self.assertEqual(OrgRole.VIEWER.label, 'Viewer')


class TestOrganization(TestCase):
    """Test cases for the Organization model."""
    
    def test_create_organization(self):
        """Test creating an organization."""
        org = OrganizationFactory()
        
        self.assertIsInstance(org, Organization)
        self.assertIsNotNone(org.name)
        self.assertTrue(org.is_active)
        self.assertIsNotNone(org.created_at)
        self.assertIsNotNone(org.updated_at)
        # Organization inherits from BaseModel, so it should have UUID primary key
        import uuid
        self.assertIsInstance(org.id, uuid.UUID)
    
    def test_organization_str_representation(self):
        """Test the string representation of an organization."""
        org = OrganizationFactory(name="Test Organization")
        self.assertEqual(str(org), "Test Organization")
    
    def test_organization_is_active_default(self):
        """Test that organizations are active by default."""
        org = Organization.objects.create(name="Test Org")
        self.assertTrue(org.is_active)
    
    def test_organization_description_optional(self):
        """Test that description is optional."""
        org = Organization.objects.create(name="Test Org")
        self.assertEqual(org.description, "")
    
    def test_organization_pii_fields(self):
        """Test that Organization has proper PII fields declared."""
        self.assertTrue(hasattr(Organization, 'pii_fields'))
        self.assertEqual(Organization.pii_fields, [])


class TestOrganizationMembership(TestCase):
    """Test cases for the OrganizationMembership model."""
    
    def setUp(self):
        self.user = UserFactory()
        self.organization = OrganizationFactory()
    
    def test_create_membership(self):
        """Test creating an organization membership."""
        membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.organization, self.organization)
        self.assertEqual(membership.role, OrgRole.ADMIN)
        self.assertFalse(membership.is_default)
    
    def test_membership_str_representation(self):
        """Test the string representation of a membership."""
        membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        expected = f"{self.user.email} - {self.organization.name} (Admin)"
        self.assertEqual(str(membership), expected)
    
    def test_membership_default_role(self):
        """Test that default role is VIEWER."""
        membership = OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization
        )
        self.assertEqual(membership.role, OrgRole.VIEWER)
    
    def test_membership_unique_constraint(self):
        """Test that user-organization pairs must be unique."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        
        with self.assertRaises(IntegrityError):
            OrganizationMembership.objects.create(
                user=self.user,
                organization=self.organization,
                role=OrgRole.VIEWER
            )
    
    def test_multiple_organizations_for_user(self):
        """Test that a user can belong to multiple organizations."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        membership1 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org1,
            role=OrgRole.ADMIN
        )
        membership2 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org2,
            role=OrgRole.VIEWER
        )
        
        self.assertEqual(self.user.organization_memberships.count(), 2)
        self.assertIn(membership1, self.user.organization_memberships.all())
        self.assertIn(membership2, self.user.organization_memberships.all())
    
    def test_multiple_users_for_organization(self):
        """Test that an organization can have multiple users."""
        user1 = UserFactory()
        user2 = UserFactory()
        
        membership1 = OrganizationMembership.objects.create(
            user=user1,
            organization=self.organization,
            role=OrgRole.ADMIN
        )
        membership2 = OrganizationMembership.objects.create(
            user=user2,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        
        self.assertEqual(self.organization.user_memberships.count(), 2)
        self.assertIn(membership1, self.organization.user_memberships.all())
        self.assertIn(membership2, self.organization.user_memberships.all())
    
    def test_one_default_membership_per_user(self):
        """Test that a user can only have one default organization."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        # Create first default membership
        membership1 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org1,
            role=OrgRole.ADMIN,
            is_default=True
        )
        
        # Try to create second default membership - should raise ValidationError
        with self.assertRaises(ValidationError) as cm:
            membership2 = OrganizationMembership(
                user=self.user,
                organization=org2,
                role=OrgRole.VIEWER,
                is_default=True
            )
            membership2.save()
        
        self.assertIn('is_default', cm.exception.message_dict)
        self.assertIn('User can only have one default organization', 
                      str(cm.exception.message_dict['is_default']))
    
    def test_can_have_multiple_non_default_memberships(self):
        """Test that a user can have multiple non-default memberships."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        org3 = OrganizationFactory()
        
        membership1 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org1,
            role=OrgRole.ADMIN,
            is_default=True
        )
        membership2 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org2,
            role=OrgRole.VIEWER,
            is_default=False
        )
        membership3 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org3,
            role=OrgRole.EDITOR,
            is_default=False
        )
        
        self.assertEqual(self.user.organization_memberships.count(), 3)
        self.assertEqual(
            self.user.organization_memberships.filter(is_default=True).count(), 
            1
        )
        self.assertEqual(
            self.user.organization_memberships.filter(is_default=False).count(), 
            2
        )
    
    def test_clean_validation_on_update(self):
        """Test that validation runs when updating an existing membership."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        # Create first default membership
        membership1 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org1,
            role=OrgRole.ADMIN,
            is_default=True
        )
        
        # Create second non-default membership
        membership2 = OrganizationMembership.objects.create(
            user=self.user,
            organization=org2,
            role=OrgRole.VIEWER,
            is_default=False
        )
        
        # Try to make the second membership default - should raise ValidationError
        with self.assertRaises(ValidationError):
            membership2.is_default = True
            membership2.save()
    
    def test_membership_pii_fields(self):
        """Test that OrganizationMembership has proper PII fields declared."""
        self.assertTrue(hasattr(OrganizationMembership, 'pii_fields'))
        self.assertEqual(OrganizationMembership.pii_fields, [])


class TestUserOrganizationMethods(TestCase):
    """Test cases for User model organization-related methods."""
    
    def setUp(self):
        self.user = UserFactory()
        self.org1 = OrganizationFactory(name="Organization 1")
        self.org2 = OrganizationFactory(name="Organization 2")
    
    def test_get_membership_existing(self):
        """Test get_membership method with existing membership."""
        membership = OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role=OrgRole.ADMIN
        )
        
        result = self.user.get_membership(self.org1)
        self.assertEqual(result, membership)
    
    def test_get_membership_nonexistent(self):
        """Test get_membership method with non-existent membership."""
        result = self.user.get_membership(self.org1)
        self.assertIsNone(result)
    
    def test_get_role_existing(self):
        """Test get_role method with existing membership."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role=OrgRole.ADMIN
        )
        
        result = self.user.get_role(self.org1)
        self.assertEqual(result, OrgRole.ADMIN)
    
    def test_get_role_nonexistent(self):
        """Test get_role method with non-existent membership."""
        result = self.user.get_role(self.org1)
        self.assertIsNone(result)
    
    def test_get_default_organization_existing(self):
        """Test get_default_organization method with existing default."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role=OrgRole.ADMIN,
            is_default=True
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org2,
            role=OrgRole.VIEWER,
            is_default=False
        )
        
        result = self.user.get_default_organization()
        self.assertEqual(result, self.org1)
    
    def test_get_default_organization_nonexistent(self):
        """Test get_default_organization method with no default set."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role=OrgRole.ADMIN,
            is_default=False
        )
        
        result = self.user.get_default_organization()
        self.assertIsNone(result)
    
    def test_organizations_many_to_many_relationship(self):
        """Test that the organizations ManyToMany relationship works."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role=OrgRole.ADMIN
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org2,
            role=OrgRole.VIEWER
        )
        
        user_orgs = self.user.organizations.all()
        self.assertEqual(user_orgs.count(), 2)
        self.assertIn(self.org1, user_orgs)
        self.assertIn(self.org2, user_orgs)
        
        # Test reverse relationship
        org1_members = self.org1.members.all()
        self.assertEqual(org1_members.count(), 1)
        self.assertIn(self.user, org1_members)


class TestOrganizationMembershipFactory(TestCase):
    """Test cases for the OrganizationMembership factory."""
    
    def test_basic_factory(self):
        """Test basic factory functionality."""
        membership = OrganizationMembershipFactory()
        
        self.assertIsInstance(membership, OrganizationMembership)
        self.assertIsInstance(membership.user, User)
        self.assertIsInstance(membership.organization, Organization)
        self.assertIn(membership.role, [choice[0] for choice in OrgRole.choices])
        self.assertFalse(membership.is_default)
    
    def test_create_default_membership(self):
        """Test factory method for default membership."""
        membership = OrganizationMembershipFactory.create_default_membership()
        self.assertTrue(membership.is_default)
    
    def test_create_admin_membership(self):
        """Test factory method for admin membership."""
        membership = OrganizationMembershipFactory.create_admin_membership()
        self.assertEqual(membership.role, OrgRole.ADMIN)
    
    def test_create_super_admin_membership(self):
        """Test factory method for super admin membership."""
        membership = OrganizationMembershipFactory.create_super_admin_membership()
        self.assertEqual(membership.role, OrgRole.SUPER_ADMIN)