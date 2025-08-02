"""
Pytest tests demonstrating conftest fixtures usage.

This module contains pytest-style tests that demonstrate the usage
of the conftest.py fixtures for FactoryBoy factories.
"""

import pytest
from core.models import User, Organization, OrganizationMembership, Project, OrgRole


@pytest.mark.django_db
def test_user_factory_fixture(user_factory):
    """Test using user_factory fixture from conftest."""
    user = user_factory.create()
    
    assert user.id is not None
    assert isinstance(user, User)
    assert user.email.endswith('@example.com')
    assert user.is_active is True


@pytest.mark.django_db
def test_org_factory_fixture(org_factory):
    """Test using org_factory fixture from conftest."""
    org = org_factory.create()
    
    assert org.id is not None
    assert isinstance(org, Organization)
    assert org.name is not None
    assert org.is_active is True


@pytest.mark.django_db
def test_member_factory_fixture(member_factory):
    """Test using member_factory fixture from conftest."""
    membership = member_factory.create()
    
    assert membership.id is not None
    assert isinstance(membership, OrganizationMembership)
    assert membership.user is not None
    assert membership.organization is not None
    assert membership.role in [choice[0] for choice in OrgRole.choices]


@pytest.mark.django_db
def test_project_factory_fixture(project_factory):
    """Test using project_factory fixture from conftest."""
    project = project_factory.create()
    
    assert project.id is not None
    assert isinstance(project, Project)
    assert project.name is not None
    assert project.organization is not None


@pytest.mark.django_db
def test_sample_user_fixture(sample_user):
    """Test using sample_user fixture from conftest."""
    assert sample_user.id is not None
    assert isinstance(sample_user, User)
    assert sample_user.email.endswith('@example.com')


@pytest.mark.django_db
def test_sample_organization_fixture(sample_organization):
    """Test using sample_organization fixture from conftest."""
    assert sample_organization.id is not None
    assert isinstance(sample_organization, Organization)
    assert sample_organization.name is not None


@pytest.mark.django_db
def test_sample_membership_fixture(sample_membership):
    """Test using sample_membership fixture from conftest."""
    assert sample_membership.id is not None
    assert isinstance(sample_membership, OrganizationMembership)
    assert sample_membership.user is not None
    assert sample_membership.organization is not None


@pytest.mark.django_db
def test_sample_project_fixture(sample_project):
    """Test using sample_project fixture from conftest."""
    assert sample_project.id is not None
    assert isinstance(sample_project, Project)
    assert sample_project.organization is not None


@pytest.mark.django_db
def test_user_with_organization_fixture(user_with_organization):
    """Test using user_with_organization fixture from conftest."""
    user, org, membership = user_with_organization
    
    assert isinstance(user, User)
    assert isinstance(org, Organization)
    assert isinstance(membership, OrganizationMembership)
    assert membership.user == user
    assert membership.organization == org
    assert membership.is_default is True


@pytest.mark.django_db
def test_organization_with_project_fixture(organization_with_project):
    """Test using organization_with_project fixture from conftest."""
    org, project = organization_with_project
    
    assert isinstance(org, Organization)
    assert isinstance(project, Project)
    assert project.organization == org


@pytest.mark.django_db
def test_complex_scenario_with_fixtures(user_factory, org_factory, member_factory, project_factory):
    """Test a complex scenario using multiple fixtures."""
    # Create organization
    org = org_factory.create(name="Test Company")
    
    # Create admin user
    admin = user_factory.create()
    admin_membership = member_factory.create(
        user=admin,
        organization=org,
        role=OrgRole.ADMIN,
        is_default=True
    )
    
    # Create regular user
    user = user_factory.create()
    user_membership = member_factory.create(
        user=user,
        organization=org,
        role=OrgRole.EDITOR
    )
    
    # Create project
    project = project_factory.create(
        organization=org,
        name="Test Project"
    )
    
    # Verify relationships
    assert org.user_memberships.count() == 2
    assert org.projects.count() == 1
    assert admin.get_role(org) == OrgRole.ADMIN
    assert user.get_role(org) == OrgRole.EDITOR
    assert admin.get_default_organization() == org
    assert project.organization == org