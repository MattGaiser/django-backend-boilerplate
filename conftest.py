"""
Pytest configuration for Django backend boilerplate.

This module provides pytest fixtures and configuration for testing
the Django application with proper database setup, user context,
and factory integration.
"""

import pytest


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This fixture is applied to all tests automatically.
    """
    pass


@pytest.fixture
def user():
    """Create a test user."""
    from core.factories import UserFactory
    return UserFactory()


@pytest.fixture
def admin_user():
    """Create an admin user."""
    from core.factories import UserFactory
    return UserFactory.create_superuser()


@pytest.fixture
def organization():
    """Create a test organization."""
    from core.factories import OrganizationFactory
    return OrganizationFactory()


@pytest.fixture
def membership(user, organization):
    """Create a test membership between user and organization."""
    from core.factories import OrganizationMembershipFactory
    return OrganizationMembershipFactory(user=user, organization=organization)


@pytest.fixture
def authenticated_user_context(user):
    """
    Set up an authenticated user context for testing signals.
    This fixture simulates having a user in the thread-local context
    as would happen during a real request.
    """
    from core.signals import set_current_user
    # Set the user in thread-local storage
    set_current_user(user)
    yield user
    # Clean up after the test
    set_current_user(None)


@pytest.fixture
def clean_user_context():
    """
    Ensure clean user context before and after test.
    This fixture ensures no user is set in thread-local storage.
    """
    from core.signals import set_current_user
    set_current_user(None)
    yield
    set_current_user(None)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This fixture is applied to all tests automatically.
    """
    pass


@pytest.fixture
def user():
    """Create a test user."""
    return UserFactory()


@pytest.fixture
def admin_user():
    """Create an admin user."""
    return UserFactory.create_superuser()


@pytest.fixture
def organization():
    """Create a test organization."""
    return OrganizationFactory()


@pytest.fixture
def membership(user, organization):
    """Create a test membership between user and organization."""
    return OrganizationMembershipFactory(user=user, organization=organization)


@pytest.fixture
def authenticated_user_context(user):
    """
    Set up an authenticated user context for testing signals.
    This fixture simulates having a user in the thread-local context
    as would happen during a real request.
    """
    # Set the user in thread-local storage
    set_current_user(user)
    yield user
    # Clean up after the test
    set_current_user(None)


@pytest.fixture
def clean_user_context():
    """
    Ensure clean user context before and after test.
    This fixture ensures no user is set in thread-local storage.
    """
    set_current_user(None)
    yield
    set_current_user(None)


class ThreadLocalTestMixin:
    """
    Mixin for TestCase classes that need to work with thread-local user context.
    Provides helper methods for setting up and cleaning up user context.
    """
    
    def set_user_context(self, user):
        """Set the current user in thread-local storage."""
        from core.signals import set_current_user
        set_current_user(user)
    
    def clear_user_context(self):
        """Clear the current user from thread-local storage."""
        from core.signals import set_current_user
        set_current_user(None)
    
    def get_user_context(self):
        """Get the current user from thread-local storage."""
        from core.signals import get_current_user
        return get_current_user()
    
    def setUp(self):
        """Ensure clean user context at start of each test."""
        super().setUp()
        self.clear_user_context()
    
    def tearDown(self):
        """Clean up user context after each test."""
        self.clear_user_context()
        super().tearDown()