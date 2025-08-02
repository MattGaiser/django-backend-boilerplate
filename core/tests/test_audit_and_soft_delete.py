"""
Enhanced tests for signal-based audit field population and soft delete behavior.

These tests specifically focus on validating the requirements from issue #16:
- Signal-based population of created_by and updated_by
- BaseModel soft delete behavior with both model calls and direct DB inspection
- Use of threadlocal helpers to simulate request context
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from django.db import connection

from core.models import User, Organization, BaseModel
from core.signals import set_current_user, get_current_user
from core.factories import UserFactory, OrganizationFactory
from conftest import ThreadLocalTestMixin


class TestSignalBasedAuditFields(TestCase, ThreadLocalTestMixin):
    """Test signal-based population of created_by and updated_by fields."""
    
    def test_created_by_populated_on_create_with_user_context(self):
        """Test that created_by is populated when user context is set."""
        # Create audit user first without any context
        self.clear_user_context()
        audit_user = UserFactory()
        
        # Now set context and create a new user
        self.set_user_context(audit_user)
        new_user = UserFactory()
        
        # Verify that created_by was populated by the signal
        self.assertEqual(new_user.created_by, audit_user)
        self.assertEqual(new_user.updated_by, audit_user)
    
    def test_updated_by_populated_on_update_with_user_context(self):
        """Test that updated_by is populated when updating with user context."""
        # Create both users without context first
        self.clear_user_context()
        audit_user = UserFactory()
        target_user = UserFactory()
        
        # Set audit user in context and update target user
        self.set_user_context(audit_user)
        target_user.full_name = "Updated Name"
        target_user.save()
        
        # Refresh from database to get updated values
        target_user.refresh_from_db()
        
        # Verify that updated_by was populated by the signal
        self.assertEqual(target_user.updated_by, audit_user)
    
    def test_no_audit_fields_when_no_user_context(self):
        """Test that audit fields remain None when no user context is set."""
        self.clear_user_context()
        
        # Create user without any context
        user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass'
        )
        
        # Audit fields should remain None
        self.assertIsNone(user.created_by)
        self.assertIsNone(user.updated_by)
    
    def test_audit_fields_with_organization_model(self):
        """Test audit field population with Organization model."""
        # Create audit user without context first
        self.clear_user_context()
        audit_user = UserFactory()
        
        # Set context and create organization
        self.set_user_context(audit_user)
        org = OrganizationFactory()
        
        # Verify audit fields
        self.assertEqual(org.created_by, audit_user)
        self.assertEqual(org.updated_by, audit_user)
    
    def test_context_cleanup_between_operations(self):
        """Test that context is properly cleaned up between operations."""
        # Create users without context first
        self.clear_user_context()
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Set first user context and create organization
        self.set_user_context(user1)
        org = OrganizationFactory()
        self.assertEqual(org.created_by, user1)
        
        # Clear context and set second user
        self.clear_user_context()
        self.set_user_context(user2)
        
        # Update organization
        org.name = "Updated Organization"
        org.save()
        org.refresh_from_db()
        
        # Should show user1 created it, user2 updated it
        self.assertEqual(org.created_by, user1)
        self.assertEqual(org.updated_by, user2)


class TestSoftDeleteBehavior(TestCase, ThreadLocalTestMixin):
    """Test BaseModel soft delete behavior with both model calls and direct DB inspection."""
    
    def test_soft_delete_sets_deleted_at(self):
        """Test that soft_delete() sets deleted_at timestamp."""
        self.clear_user_context()
        user = UserFactory()
        self.assertIsNone(user.deleted_at)
        self.assertFalse(user.is_deleted)
        
        # Perform soft delete
        user.soft_delete()
        
        # Verify soft delete behavior
        self.assertIsNotNone(user.deleted_at)
        self.assertTrue(user.is_deleted)
        self.assertLessEqual(user.deleted_at, timezone.now())
    
    def test_soft_delete_preserves_record_in_database(self):
        """Test that soft deleted records are preserved in database."""
        self.clear_user_context()
        user = UserFactory()
        original_email = user.email
        
        # Soft delete the user
        user.soft_delete()
        
        # The record should still be retrievable by ID
        # (this tests that it's preserved in the database)
        user_from_db = User.objects.get(id=user.id)
        self.assertEqual(user_from_db.email, original_email)
        self.assertTrue(user_from_db.is_deleted)
        self.assertIsNotNone(user_from_db.deleted_at)
    
    def test_model_delete_vs_soft_delete(self):
        """Test difference between model.delete() and soft_delete()."""
        self.clear_user_context()
        user1 = UserFactory()
        user2 = UserFactory()
        user1_id = user1.id
        user2_id = user2.id
        
        # Soft delete user1
        user1.soft_delete()
        
        # Hard delete user2 (Django's default delete)
        user2.delete()
        
        # Test retrieval behavior
        # Soft deleted record should still be retrievable
        try:
            soft_deleted_user = User.objects.get(id=user1_id)
            self.assertTrue(soft_deleted_user.is_deleted)
            soft_delete_exists = True
        except User.DoesNotExist:
            soft_delete_exists = False
        
        # Hard deleted record should not be retrievable
        try:
            User.objects.get(id=user2_id)
            hard_delete_exists = True
        except User.DoesNotExist:
            hard_delete_exists = False
        
        # Assertions
        self.assertTrue(soft_delete_exists, "Soft deleted record should still exist")
        self.assertFalse(hard_delete_exists, "Hard deleted record should not exist")
    
    def test_is_deleted_property(self):
        """Test the is_deleted property accurately reflects soft delete state."""
        self.clear_user_context()
        user = UserFactory()
        
        # Initially not deleted
        self.assertFalse(user.is_deleted)
        
        # After soft delete
        user.soft_delete()
        self.assertTrue(user.is_deleted)
        
        # Manually setting deleted_at should also work
        other_user = UserFactory()
        other_user.deleted_at = timezone.now()
        self.assertTrue(other_user.is_deleted)
    
    def test_soft_delete_uses_update_fields(self):
        """Test that soft_delete only updates the deleted_at field using update_fields."""
        self.clear_user_context()
        user = UserFactory()
        original_updated_at = user.updated_at
        
        # Wait a moment to ensure timestamp difference would be visible
        import time
        time.sleep(0.1)
        
        # Perform soft delete
        user.soft_delete()
        
        # Refresh from database
        user.refresh_from_db()
        
        # deleted_at should be set, but updated_at should NOT change
        # because soft_delete uses update_fields=['deleted_at']
        self.assertIsNotNone(user.deleted_at)
        self.assertEqual(user.updated_at, original_updated_at)


class TestAuditFieldsWithSoftDelete(TestCase, ThreadLocalTestMixin):
    """Test interaction between audit fields and soft delete."""
    
    def test_soft_delete_does_not_trigger_audit_signals(self):
        """Test that soft_delete does not update audit fields due to update_fields usage."""
        # Create users without context first to avoid circular reference
        self.clear_user_context()
        creator = UserFactory()
        deleter = UserFactory()
        
        # Create user with creator context
        self.set_user_context(creator)
        user = UserFactory()
        self.assertEqual(user.created_by, creator)
        original_updated_by = user.updated_by
        
        # Soft delete with deleter context
        self.set_user_context(deleter)
        user.soft_delete()
        user.refresh_from_db()
        
        # Verify soft delete worked but audit fields unchanged
        # (because soft_delete uses update_fields which bypasses signals)
        self.assertEqual(user.created_by, creator)
        self.assertEqual(user.updated_by, original_updated_by)  # Should remain unchanged
        self.assertTrue(user.is_deleted)
    
    def test_manual_save_after_setting_deleted_at_triggers_audit(self):
        """Test that manually setting deleted_at and calling save() triggers audit signals."""
        # Create users without context first
        self.clear_user_context()
        creator = UserFactory()
        deleter = UserFactory()
        
        # Create user with creator context
        self.set_user_context(creator)
        user = UserFactory()
        self.assertEqual(user.created_by, creator)
        
        # Manually set deleted_at and save with deleter context
        self.set_user_context(deleter)
        user.deleted_at = timezone.now()
        user.save()  # This should trigger audit signals
        user.refresh_from_db()
        
        # Verify audit trail
        self.assertEqual(user.created_by, creator)
        self.assertEqual(user.updated_by, deleter)
        self.assertTrue(user.is_deleted)


class TestThreadLocalHelpers(TestCase):
    """Test thread-local helper functions for simulating request context."""
    
    def setUp(self):
        """Ensure clean state before each test."""
        super().setUp()
        set_current_user(None)
    
    def tearDown(self):
        """Clean up after each test."""
        set_current_user(None)
        super().tearDown()
    
    def test_set_and_get_current_user(self):
        """Test basic thread-local user storage functionality."""
        user = UserFactory()
        
        # Initially no user
        self.assertIsNone(get_current_user())
        
        # Set user
        set_current_user(user)
        self.assertEqual(get_current_user(), user)
        
        # Clear user
        set_current_user(None)
        self.assertIsNone(get_current_user())
    
    def test_thread_local_isolation(self):
        """Test that thread-local storage is properly isolated."""
        import threading
        import time
        
        user1 = UserFactory()
        user2 = UserFactory()
        results = {}
        
        def thread_function(user, thread_id):
            set_current_user(user)
            time.sleep(0.1)  # Allow context switching
            results[thread_id] = get_current_user()
            set_current_user(None)
        
        # Start two threads with different users
        thread1 = threading.Thread(target=thread_function, args=(user1, 'thread1'))
        thread2 = threading.Thread(target=thread_function, args=(user2, 'thread2'))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Each thread should have maintained its own user
        self.assertEqual(results['thread1'], user1)
        self.assertEqual(results['thread2'], user2)
    
    def test_authenticated_user_simulation(self):
        """Test simulating authenticated user context for signals."""
        # Create user without context first
        set_current_user(None)
        user = UserFactory()
        
        # Mock the is_authenticated property (it's read-only on Django's User)
        # We'll use a simple workaround since the signal checks is_authenticated
        set_current_user(user)
        
        # Create an organization (should trigger audit signals)
        org = OrganizationFactory()
        
        # Verify signals worked (user is considered authenticated by default)
        self.assertEqual(org.created_by, user)
        self.assertEqual(org.updated_by, user)
        
        # Clean up
        set_current_user(None)