"""
Pytest configuration and shared fixtures for the Django backend boilerplate.

This module provides common fixtures and configurations that can be used
across all test modules in the project.
"""

import pytest


@pytest.fixture
def user_factory():
    """
    Fixture that provides UserFactory for creating test users.

    Returns:
        UserFactory: Factory class for creating User instances
    """
    from core.factories import UserFactory

    return UserFactory


@pytest.fixture
def org_factory():
    """
    Fixture that provides OrganizationFactory for creating test organizations.

    Returns:
        OrganizationFactory: Factory class for creating Organization instances
    """
    from core.factories import OrganizationFactory

    return OrganizationFactory


@pytest.fixture
def member_factory():
    """
    Fixture that provides OrganizationMembershipFactory for creating test memberships.

    Returns:
        OrganizationMembershipFactory: Factory class for creating OrganizationMembership instances
    """
    from core.factories import OrganizationMembershipFactory

    return OrganizationMembershipFactory


@pytest.fixture
def project_factory():
    """
    Fixture that provides ProjectFactory for creating test projects.

    Returns:
        ProjectFactory: Factory class for creating Project instances
    """
    from core.factories import ProjectFactory

    return ProjectFactory


@pytest.fixture
def sample_user(user_factory):
    """
    Fixture that creates a sample user for testing.

    Returns:
        User: A created User instance with default test data
    """
    return user_factory.create()


@pytest.fixture
def sample_organization(org_factory):
    """
    Fixture that creates a sample organization for testing.

    Returns:
        Organization: A created Organization instance with default test data
    """
    return org_factory.create()


@pytest.fixture
def sample_membership(member_factory):
    """
    Fixture that creates a sample organization membership for testing.

    Returns:
        OrganizationMembership: A created OrganizationMembership instance
    """
    return member_factory.create()


@pytest.fixture
def sample_project(project_factory):
    """
    Fixture that creates a sample project for testing.

    Returns:
        Project: A created Project instance with default test data
    """
    return project_factory.create()


@pytest.fixture
def user_with_organization(user_factory, org_factory, member_factory):
    """
    Fixture that creates a user with an organization membership.

    Returns:
        tuple: (User, Organization, OrganizationMembership)
    """
    user = user_factory.create()
    org = org_factory.create()
    membership = member_factory.create(user=user, organization=org, is_default=True)
    return user, org, membership


@pytest.fixture
def organization_with_project(org_factory, project_factory):
    """
    Fixture that creates an organization with a project.

    Returns:
        tuple: (Organization, Project)
    """
    org = org_factory.create()
    project = project_factory.create(organization=org)
    return org, project
