"""
Tests for FactoryBoy factories to ensure they produce valid records.

This module contains tests that verify all factories create valid model instances
with all required fields properly set.
"""

from django.contrib.auth import authenticate
from django.test import TestCase

from core.factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
    ProjectFactory,
    UserFactory,
)
from core.models import Organization, OrganizationMembership, OrgRole, Project, User


class TestUserFactory(TestCase):
    """Test cases for UserFactory."""

    def test_user_factory_creates_valid_user(self):
        """Test that UserFactory creates a valid User instance."""
        user = UserFactory.create()

        # Verify the user is created and saved
        self.assertIsNotNone(user.id)
        self.assertIsInstance(user, User)

        # Verify required fields are set
        self.assertIsNotNone(user.email)
        self.assertIsNotNone(user.full_name)
        self.assertTrue(user.email.endswith("@example.com"))

        # Verify default values
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.language, "en")
        self.assertEqual(user.timezone, "UTC")

        # Verify user can be retrieved from database
        db_user = User.objects.get(id=user.id)
        self.assertEqual(db_user.email, user.email)

    def test_user_factory_sets_password(self):
        """Test that UserFactory sets a password for the user."""
        user = UserFactory.create(password="custom_password")

        # Verify password is set and works
        self.assertTrue(user.check_password("custom_password"))

        # Verify user can authenticate
        authenticated_user = authenticate(
            username=user.email, password="custom_password"
        )
        self.assertEqual(authenticated_user, user)

    def test_user_factory_default_password(self):
        """Test that UserFactory sets a default password when none provided."""
        user = UserFactory.create()

        # Verify default password works
        self.assertTrue(user.check_password("testpass123"))

    def test_user_factory_superuser_creation(self):
        """Test creating a superuser with UserFactory."""
        user = UserFactory.create_superuser()

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_user_factory_staff_user_creation(self):
        """Test creating a staff user with UserFactory."""
        user = UserFactory.create_staff_user()

        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_user_factory_unique_emails(self):
        """Test that UserFactory creates unique emails for multiple users."""
        users = UserFactory.create_batch(5)
        emails = [user.email for user in users]

        # Verify all emails are unique
        self.assertEqual(len(emails), len(set(emails)))


class TestOrganizationFactory(TestCase):
    """Test cases for OrganizationFactory."""

    def test_organization_factory_creates_valid_organization(self):
        """Test that OrganizationFactory creates a valid Organization instance."""
        org = OrganizationFactory.create()

        # Verify the organization is created and saved
        self.assertIsNotNone(org.id)
        self.assertIsInstance(org, Organization)

        # Verify required fields are set
        self.assertIsNotNone(org.name)
        self.assertIsNotNone(org.description)

        # Verify default values
        self.assertTrue(org.is_active)

        # Verify organization can be retrieved from database
        db_org = Organization.objects.get(id=org.id)
        self.assertEqual(db_org.name, org.name)

    def test_organization_factory_batch_creation(self):
        """Test creating multiple organizations with OrganizationFactory."""
        orgs = OrganizationFactory.create_batch(3)

        self.assertEqual(len(orgs), 3)
        for org in orgs:
            self.assertIsInstance(org, Organization)
            self.assertIsNotNone(org.id)
            self.assertTrue(org.is_active)

        # Verify all organizations have unique names
        names = [org.name for org in orgs]
        self.assertEqual(len(names), len(set(names)))


class TestOrganizationMembershipFactory(TestCase):
    """Test cases for OrganizationMembershipFactory."""

    def test_membership_factory_creates_valid_membership(self):
        """Test that OrganizationMembershipFactory creates a valid membership."""
        membership = OrganizationMembershipFactory.create()

        # Verify the membership is created and saved
        self.assertIsNotNone(membership.id)
        self.assertIsInstance(membership, OrganizationMembership)

        # Verify required fields are set
        self.assertIsNotNone(membership.user)
        self.assertIsNotNone(membership.organization)
        self.assertIn(membership.role, [choice[0] for choice in OrgRole.choices])

        # Verify default values
        self.assertFalse(membership.is_default)

        # Verify membership can be retrieved from database
        db_membership = OrganizationMembership.objects.get(id=membership.id)
        self.assertEqual(db_membership.user, membership.user)
        self.assertEqual(db_membership.organization, membership.organization)

    def test_membership_factory_creates_related_objects(self):
        """Test that OrganizationMembershipFactory creates related User and Organization."""
        membership = OrganizationMembershipFactory.create()

        # Verify related objects exist in database
        self.assertTrue(User.objects.filter(id=membership.user.id).exists())
        self.assertTrue(
            Organization.objects.filter(id=membership.organization.id).exists()
        )

    def test_membership_factory_default_membership(self):
        """Test creating a default membership."""
        membership = OrganizationMembershipFactory.create_default_membership()

        self.assertTrue(membership.is_default)

    def test_membership_factory_admin_membership(self):
        """Test creating an admin membership."""
        membership = OrganizationMembershipFactory.create_admin_membership()

        self.assertEqual(membership.role, OrgRole.ADMIN)

    def test_membership_factory_super_admin_membership(self):
        """Test creating a super admin membership."""
        membership = OrganizationMembershipFactory.create_super_admin_membership()

        self.assertEqual(membership.role, OrgRole.SUPER_ADMIN)

    def test_membership_factory_unique_constraint(self):
        """Test that membership factory respects unique constraint."""
        user = UserFactory.create()
        org = OrganizationFactory.create()

        # Create first membership
        membership1 = OrganizationMembershipFactory.create(user=user, organization=org)

        # Try to create duplicate membership (should fail)
        with self.assertRaises(Exception):  # Django will raise IntegrityError
            OrganizationMembershipFactory.create(user=user, organization=org)


class TestProjectFactory(TestCase):
    """Test cases for ProjectFactory."""

    def test_project_factory_creates_valid_project(self):
        """Test that ProjectFactory creates a valid Project instance."""
        project = ProjectFactory.create()

        # Verify the project is created and saved
        self.assertIsNotNone(project.id)
        self.assertIsInstance(project, Project)

        # Verify required fields are set
        self.assertIsNotNone(project.name)
        self.assertIsNotNone(project.organization)
        self.assertIn(
            project.status, [choice[0] for choice in Project.StatusChoices.choices]
        )

        # Verify default values
        self.assertTrue(project.is_active)

        # Verify project can be retrieved from database
        db_project = Project.objects.get(id=project.id)
        self.assertEqual(db_project.name, project.name)

    def test_project_factory_creates_related_organization(self):
        """Test that ProjectFactory creates related Organization."""
        project = ProjectFactory.create()

        # Verify related organization exists in database
        self.assertTrue(
            Organization.objects.filter(id=project.organization.id).exists()
        )

    def test_project_factory_date_consistency(self):
        """Test that ProjectFactory creates consistent start and end dates."""
        project = ProjectFactory.create()

        if project.start_date and project.end_date:
            self.assertLessEqual(project.start_date, project.end_date)

    def test_project_factory_active_project(self):
        """Test creating an active project."""
        project = ProjectFactory.create_active_project()

        self.assertEqual(project.status, Project.StatusChoices.ACTIVE)
        self.assertTrue(project.is_active)

    def test_project_factory_completed_project(self):
        """Test creating a completed project."""
        project = ProjectFactory.create_completed_project()

        self.assertEqual(project.status, Project.StatusChoices.COMPLETED)
        self.assertFalse(project.is_active)

    def test_project_factory_batch_creation(self):
        """Test creating multiple projects with ProjectFactory."""
        projects = ProjectFactory.create_batch(3)

        self.assertEqual(len(projects), 3)
        for project in projects:
            self.assertIsInstance(project, Project)
            self.assertIsNotNone(project.id)
            self.assertIsNotNone(project.organization)


class TestFactoryIntegration(TestCase):
    """Integration tests for multiple factories working together."""

    def test_creating_complete_organization_structure(self):
        """Test creating a complete organization with users, memberships, and projects."""
        # Create organization
        org = OrganizationFactory.create()

        # Create users with memberships
        admin_user = UserFactory.create()
        admin_membership = OrganizationMembershipFactory.create(
            user=admin_user, organization=org, role=OrgRole.ADMIN, is_default=True
        )

        editor_user = UserFactory.create()
        editor_membership = OrganizationMembershipFactory.create(
            user=editor_user, organization=org, role=OrgRole.EDITOR
        )

        # Create projects
        active_project = ProjectFactory.create(
            organization=org, status=Project.StatusChoices.ACTIVE
        )
        completed_project = ProjectFactory.create(
            organization=org, status=Project.StatusChoices.COMPLETED
        )

        # Verify relationships
        self.assertEqual(org.user_memberships.count(), 2)
        self.assertEqual(org.projects.count(), 2)
        self.assertEqual(admin_user.organization_memberships.count(), 1)
        self.assertEqual(editor_user.organization_memberships.count(), 1)

        # Verify roles
        self.assertEqual(admin_user.get_role(org), OrgRole.ADMIN)
        self.assertEqual(editor_user.get_role(org), OrgRole.EDITOR)

        # Verify default organization
        self.assertEqual(admin_user.get_default_organization(), org)
        self.assertIsNone(editor_user.get_default_organization())

    def test_factory_inheritance_from_basemodel(self):
        """Test that all factory-created models properly inherit BaseModel functionality."""
        org = OrganizationFactory.create()
        user = UserFactory.create()
        membership = OrganizationMembershipFactory.create()
        project = ProjectFactory.create()

        models = [org, user, membership, project]

        for model in models:
            # Verify BaseModel fields are set
            self.assertIsNotNone(model.id)
            self.assertIsNotNone(model.created_at)
            self.assertIsNotNone(model.updated_at)
            self.assertIsNone(model.deleted_at)

            # Verify soft delete functionality
            self.assertFalse(model.is_deleted)
            model.soft_delete()
            self.assertTrue(model.is_deleted)
            self.assertIsNotNone(model.deleted_at)
