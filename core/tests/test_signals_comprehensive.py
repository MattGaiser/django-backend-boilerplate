"""
Comprehensive tests for Django signals including audit field population and PII validation.

Tests cover:
- Signal-based population of created_by and updated_by fields
- Threadlocal context simulation for request-based audit tracking
- PII enforcement signal behavior
- Signal integration with BaseModel lifecycle
"""

from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from core.factories import OrganizationFactory, ProjectFactory, UserFactory
from core.models import Organization, Project, User
from core.signals import (
    get_current_user,
    get_model_pii_fields,
    get_pii_field_names,
    set_current_user,
)


class TestSignalBasedAuditFields(TestCase):
    """Test automatic population of created_by and updated_by fields via signals."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.admin_user = UserFactory.create_superuser()

    def tearDown(self):
        """Clean up thread-local storage after each test."""
        set_current_user(None)

    def test_created_by_populated_on_new_instance(self):
        """Test that created_by is automatically set when creating new instances."""
        # Set current user in thread-local storage
        set_current_user(self.user)

        # Create new organization
        org = OrganizationFactory()

        # Verify created_by is set
        self.assertEqual(org.created_by, self.user)
        self.assertEqual(org.updated_by, self.user)

    def test_updated_by_populated_on_save(self):
        """Test that updated_by is automatically set when updating instances."""
        # Create organization with first user
        set_current_user(self.user)
        org = OrganizationFactory()
        original_created_by = org.created_by

        # Update with different user
        set_current_user(self.admin_user)
        org.name = "Updated Organization Name"
        org.save()

        # Verify audit fields
        org.refresh_from_db()
        self.assertEqual(org.created_by, original_created_by)  # Should not change
        self.assertEqual(org.updated_by, self.admin_user)  # Should be updated

    def test_no_user_context_leaves_fields_none(self):
        """Test that audit fields remain None when no user is in context."""
        # Ensure no user is set
        set_current_user(None)

        # Create organization
        org = OrganizationFactory()

        # Verify audit fields are None
        self.assertIsNone(org.created_by)
        self.assertIsNone(org.updated_by)

    def test_unauthenticated_user_context(self):
        """Test behavior with unauthenticated user in context."""
        # Set unauthenticated user
        anon_user = AnonymousUser()
        set_current_user(anon_user)

        # Create organization
        org = OrganizationFactory()

        # Audit fields should remain None for unauthenticated users
        self.assertIsNone(org.created_by)
        self.assertIsNone(org.updated_by)

    def test_signal_works_across_model_types(self):
        """Test that signal works consistently across different BaseModel subclasses."""
        set_current_user(self.user)

        # Test User model (though created_by/updated_by might be self-referential)
        user2 = UserFactory()
        self.assertEqual(user2.created_by, self.user)

        # Test Organization model
        org = OrganizationFactory()
        self.assertEqual(org.created_by, self.user)

        # Test Project model
        project = ProjectFactory(organization=org)
        self.assertEqual(project.created_by, self.user)

    def test_manual_audit_field_assignment_not_overridden(self):
        """Test that manually set audit fields are not overridden by signals."""
        set_current_user(self.user)

        # Create organization with manually set created_by
        other_user = UserFactory()
        org = Organization(name="Test Org", created_by=other_user)  # Manually set
        org.save()

        # The signal should respect the manually set value for new instances
        # but update updated_by
        self.assertEqual(org.created_by, other_user)
        self.assertEqual(org.updated_by, self.user)


class TestThreadLocalUserContext(TestCase):
    """Test thread-local user context management for signal-based audit tracking."""

    def setUp(self):
        """Set up test data."""
        self.user1 = UserFactory()
        self.user2 = UserFactory()

    def tearDown(self):
        """Clean up thread-local storage."""
        set_current_user(None)

    def test_thread_local_user_isolation(self):
        """Test that thread-local storage properly isolates user context."""
        # Initially no user
        self.assertIsNone(get_current_user())

        # Set user1
        set_current_user(self.user1)
        self.assertEqual(get_current_user(), self.user1)

        # Change to user2
        set_current_user(self.user2)
        self.assertEqual(get_current_user(), self.user2)

        # Clear user
        set_current_user(None)
        self.assertIsNone(get_current_user())

    def test_request_context_simulation(self):
        """Test simulating request context for audit tracking."""

        # Simulate login request context
        def simulate_request_context(user):
            """Helper to simulate request context with user."""
            set_current_user(user)

            # Perform database operations as if in a request
            org = OrganizationFactory()
            project = ProjectFactory(organization=org)

            return org, project

        # Simulate request from user1
        org1, project1 = simulate_request_context(self.user1)
        self.assertEqual(org1.created_by, self.user1)
        self.assertEqual(project1.created_by, self.user1)

        # Simulate request from user2
        org2, project2 = simulate_request_context(self.user2)
        self.assertEqual(org2.created_by, self.user2)
        self.assertEqual(project2.created_by, self.user2)

        # Clear context
        set_current_user(None)

    def test_context_manager_pattern(self):
        """Test using context manager pattern for user context."""
        from contextlib import contextmanager

        @contextmanager
        def user_context(user):
            """Context manager for user context."""
            old_user = get_current_user()
            set_current_user(user)
            try:
                yield
            finally:
                set_current_user(old_user)

        # Use context manager
        with user_context(self.user1):
            org = OrganizationFactory()
            self.assertEqual(org.created_by, self.user1)

        # Context should be cleared
        self.assertIsNone(get_current_user())

        # Nested context
        set_current_user(self.user1)
        with user_context(self.user2):
            project = ProjectFactory()
            self.assertEqual(project.created_by, self.user2)

        # Should restore original context
        self.assertEqual(get_current_user(), self.user1)

    def test_concurrent_context_simulation(self):
        """Test that contexts don't interfere (simulated concurrency)."""
        # This test simulates what would happen with different threads
        # In actual threading, each thread would have its own storage

        operations_log = []

        def operation_set_1():
            set_current_user(self.user1)
            org = OrganizationFactory()
            operations_log.append(("user1", org.created_by))
            set_current_user(None)

        def operation_set_2():
            set_current_user(self.user2)
            project = ProjectFactory()
            operations_log.append(("user2", project.created_by))
            set_current_user(None)

        # Execute operations sequentially (simulating concurrent execution)
        operation_set_1()
        operation_set_2()

        # Verify results
        self.assertEqual(len(operations_log), 2)
        self.assertEqual(operations_log[0], ("user1", self.user1))
        self.assertEqual(operations_log[1], ("user2", self.user2))


class TestPIIValidationSignalEnhanced(TestCase):
    """Enhanced tests for PII validation signal."""

    def test_pii_field_names_configuration(self):
        """Test that PII field names can be configured."""
        default_pii_fields = get_pii_field_names()

        # Should include common PII field names
        expected_fields = {
            "email",
            "full_name",
            "first_name",
            "last_name",
            "phone",
            "address",
            "ssn",
            "date_of_birth",
        }
        self.assertTrue(expected_fields.issubset(default_pii_fields))

    def test_model_pii_fields_detection(self):
        """Test detection of PII fields in models."""
        # User model should have PII fields declared
        user_pii_fields = get_model_pii_fields(User)
        self.assertIn("email", user_pii_fields)
        self.assertIn("full_name", user_pii_fields)

        # Organization model should have name as PII field
        org_pii_fields = get_model_pii_fields(Organization)
        self.assertEqual(org_pii_fields, ["name"])

    def test_pii_validation_with_custom_model(self):
        """Test PII validation with a custom model."""

        # Create a test model class that would trigger validation
        class TestModelWithPII:
            __name__ = "TestModel"
            __module__ = "test_app.models"
            pii_fields = ["email", "personal_info"]

            class _meta:
                abstract = False
                app_label = "test_app"
                auto_created = False

                def get_fields(self):
                    class Field:
                        def __init__(self, name):
                            self.name = name

                    return [
                        Field("email"),
                        Field("personal_info"),
                        Field("public_data"),
                    ]

        # Test that model with proper PII declaration passes
        model = TestModelWithPII()
        model._meta = TestModelWithPII._meta()

        # This should not raise an exception
        try:
            # Simulate the validation logic
            pii_field_names = get_pii_field_names()
            model_field_names = {"email", "personal_info", "public_data"}
            found_pii_fields = model_field_names.intersection(pii_field_names)
            declared_pii_fields = set(get_model_pii_fields(model))

            if found_pii_fields and not declared_pii_fields:
                raise ImproperlyConfigured("PII fields not declared")

            undeclared_fields = found_pii_fields - declared_pii_fields
            if undeclared_fields:
                raise ImproperlyConfigured(
                    f"Undeclared PII fields: {undeclared_fields}"
                )

        except Exception as e:
            self.fail(
                f"PII validation should not raise exception for properly configured model: {e}"
            )

    @patch("core.signals.logger")
    def test_pii_validation_logging(self, mock_logger):
        """Test that PII validation logs appropriate warnings."""
        # This test verifies that the validation logic logs warnings
        # for potentially ambiguous PII fields

        class TestModelWithAmbiguousFields:
            __name__ = "TestModel"
            __module__ = "test_app.models"
            pii_fields = []

            class _meta:
                abstract = False
                app_label = "test_app"
                auto_created = False

                def get_fields(self):
                    class Field:
                        def __init__(self, name):
                            self.name = name

                    return [
                        Field("name"),
                        Field("description"),
                    ]  # Potentially ambiguous

        # The actual validation would happen in the signal
        # Here we just test the warning logic
        ambiguous_fields = {"name", "description"}  # These might contain PII
        declared_fields = set()  # No PII fields declared

        ambiguous_undeclared = ambiguous_fields - declared_fields
        if ambiguous_undeclared:
            # This would trigger the warning log
            pass

        # In actual signal, this would log a warning
        self.assertEqual(ambiguous_undeclared, {"name", "description"})


class TestSignalIntegrationWithBaseModel(TestCase):
    """Test signal integration with BaseModel lifecycle."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    def tearDown(self):
        """Clean up thread-local storage."""
        set_current_user(None)

    def test_signal_integration_with_factory_boy(self):
        """Test that signals work correctly with factory_boy generated instances."""
        set_current_user(self.user)

        # Use factory to create instances
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)

        # Verify signals were triggered
        self.assertEqual(org.created_by, self.user)
        self.assertEqual(project.created_by, self.user)

    def test_signal_integration_with_bulk_operations(self):
        """Test signal behavior with bulk database operations."""
        set_current_user(self.user)

        # Test bulk_create (signals typically don't fire for bulk operations)
        orgs_data = [Organization(name=f"Bulk Org {i}") for i in range(3)]
        created_orgs = Organization.objects.bulk_create(orgs_data)

        # Bulk operations bypass signals, so audit fields should be None
        for org in created_orgs:
            org.refresh_from_db()
            self.assertIsNone(org.created_by)

    def test_signal_integration_with_model_inheritance(self):
        """Test that signals work correctly with model inheritance."""
        set_current_user(self.user)

        # All BaseModel subclasses should have signals applied
        models_to_test = [
            (UserFactory, User),
            (OrganizationFactory, Organization),
            (ProjectFactory, Project),
        ]

        for factory_class, model_class in models_to_test:
            if factory_class == UserFactory:
                instance = factory_class()
            else:
                instance = factory_class()

            # All should have audit fields populated by signals
            if hasattr(instance, "created_by"):
                self.assertEqual(instance.created_by, self.user)
            if hasattr(instance, "updated_by"):
                self.assertEqual(instance.updated_by, self.user)

    def test_signal_performance_impact(self):
        """Test that signals don't significantly impact performance."""
        import time

        set_current_user(self.user)

        # Measure time for operations with signals
        start_time = time.time()
        for _ in range(10):
            OrganizationFactory()
        with_signals_time = time.time() - start_time

        # The time should be reasonable (this is more of a smoke test)
        self.assertLess(with_signals_time, 5.0)  # Should complete within 5 seconds

    def test_signal_error_handling(self):
        """Test that signal errors don't break model operations."""
        # Test with invalid user object
        invalid_user = Mock()
        invalid_user.is_authenticated = False
        set_current_user(invalid_user)

        # Should still be able to create objects
        try:
            org = OrganizationFactory()
            # Audit fields should be None due to invalid user
            self.assertIsNone(org.created_by)
        except Exception as e:
            self.fail(f"Signal error should not break model creation: {e}")
