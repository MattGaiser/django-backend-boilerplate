"""
Comprehensive tests for soft delete functionality.

Tests cover:
- BaseModel soft delete behavior (deleted_at set, excluded from default queryset)
- Direct DB inspection for soft delete verification
- Manager methods for accessing soft deleted records
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from django.db import connection
from django.core.exceptions import ValidationError

from core.models import User, Organization, Project
from core.factories import UserFactory, OrganizationFactory, ProjectFactory


class TestSoftDeleteBehavior(TestCase):
    """Test soft delete functionality across BaseModel subclasses."""
    
    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.org = OrganizationFactory()
        self.project = ProjectFactory()
    
    def test_soft_delete_sets_deleted_at(self):
        """Test that soft_delete() sets deleted_at timestamp."""
        # Verify initial state
        self.assertIsNone(self.user.deleted_at)
        self.assertFalse(self.user.is_deleted)
        
        # Perform soft delete
        before_delete = timezone.now()
        self.user.soft_delete()
        after_delete = timezone.now()
        
        # Verify deleted_at is set within expected time range
        self.assertIsNotNone(self.user.deleted_at)
        self.assertTrue(self.user.is_deleted)
        self.assertGreaterEqual(self.user.deleted_at, before_delete)
        self.assertLessEqual(self.user.deleted_at, after_delete)
    
    def test_soft_delete_excluded_from_default_queryset(self):
        """Test that soft deleted records are excluded from default queryset."""
        # Create multiple test records
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        # Verify all are in default queryset initially
        self.assertEqual(User.objects.count(), 4)  # Including self.user from setUp
        
        # Soft delete one record
        user2.soft_delete()
        
        # Verify default queryset excludes soft deleted record
        self.assertEqual(User.objects.count(), 3)
        self.assertNotIn(user2, User.objects.all())
        self.assertIn(user1, User.objects.all())
        self.assertIn(user3, User.objects.all())
        
        # Soft delete another record
        user3.soft_delete()
        
        # Verify both are excluded
        self.assertEqual(User.objects.count(), 2)
        self.assertNotIn(user2, User.objects.all())
        self.assertNotIn(user3, User.objects.all())
        self.assertIn(user1, User.objects.all())
    
    def test_all_objects_manager_includes_soft_deleted(self):
        """Test that all_objects manager includes soft deleted records."""
        # Create test records
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Count before soft delete
        total_count = User.all_objects.count()
        active_count = User.objects.count()
        self.assertEqual(total_count, active_count)
        
        # Soft delete one record
        user2.soft_delete()
        
        # Verify counts
        self.assertEqual(User.all_objects.count(), total_count)  # Total unchanged
        self.assertEqual(User.objects.count(), active_count - 1)  # Active reduced by 1
        
        # Verify record is in all_objects but not in objects
        self.assertIn(user2, User.all_objects.all())
        self.assertNotIn(user2, User.objects.all())
    
    def test_soft_delete_manager_methods(self):
        """Test custom manager methods for soft delete functionality."""
        # Create test records
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        # Soft delete some records
        user2.soft_delete()
        user3.soft_delete()
        
        # Test all_with_deleted method
        all_users = User.objects.all_with_deleted()
        self.assertEqual(all_users.count(), 4)  # Including self.user from setUp
        self.assertIn(user1, all_users)
        self.assertIn(user2, all_users)
        self.assertIn(user3, all_users)
        
        # Test deleted_only method
        deleted_users = User.objects.deleted_only()
        self.assertEqual(deleted_users.count(), 2)
        self.assertNotIn(user1, deleted_users)
        self.assertIn(user2, deleted_users)
        self.assertIn(user3, deleted_users)
    
    def test_soft_delete_works_across_models(self):
        """Test that soft delete works consistently across different BaseModel subclasses."""
        # Test on Organization - count before and after
        org_count_before = Organization.objects.count()
        self.org.soft_delete()
        self.assertEqual(Organization.objects.count(), org_count_before - 1)
        self.assertGreater(Organization.all_objects.count(), Organization.objects.count())
        
        # Test on Project - count before and after
        project_count_before = Project.objects.count()
        self.project.soft_delete()
        self.assertEqual(Project.objects.count(), project_count_before - 1)
        self.assertGreater(Project.all_objects.count(), Project.objects.count())
    
    def test_hard_delete_still_works(self):
        """Test that hard delete (actual deletion) still works when needed."""
        user = UserFactory()
        user_id = user.id
        
        # Verify record exists
        self.assertTrue(User.all_objects.filter(id=user_id).exists())
        
        # Hard delete
        user.delete()
        
        # Verify record is completely gone
        self.assertFalse(User.all_objects.filter(id=user_id).exists())
        self.assertFalse(User.objects.filter(id=user_id).exists())


class TestSoftDeleteDirectDBInspection(TestCase):
    """Test soft delete behavior with direct database inspection."""
    
    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
    
    def test_soft_delete_db_state_inspection(self):
        """Test soft delete using direct database inspection."""
        user_id = str(self.user.id)
        
        # Check initial DB state using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT deleted_at FROM core_user WHERE id = %s",
                [user_id]
            )
            result = cursor.fetchone()
            self.assertIsNotNone(result)  # Record should exist
            self.assertIsNone(result[0])  # deleted_at should be NULL
        
        # Perform soft delete
        self.user.soft_delete()
        
        # Check DB state after soft delete using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT deleted_at FROM core_user WHERE id = %s",
                [user_id]
            )
            result = cursor.fetchone()
            self.assertIsNotNone(result)  # Record should exist
            self.assertIsNotNone(result[0])  # deleted_at should have a timestamp
        
        # Verify the timestamp is recent
        deleted_at = result[0]
        time_diff = timezone.now() - deleted_at
        self.assertLess(time_diff.total_seconds(), 10)  # Within 10 seconds
    
    def test_default_queryset_exclusion_via_sql(self):
        """Test that default queryset exclusion works at the SQL level."""
        # Create multiple users
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        # Soft delete one user
        user2.soft_delete()
        
        # Get the SQL query used by the default manager
        queryset = User.objects.all()
        sql_query = str(queryset.query)
        
        # Verify that the SQL includes the filter for deleted_at IS NULL
        self.assertIn('deleted_at', sql_query.lower())
        self.assertIn('is null', sql_query.lower())
        
        # Count records using raw SQL with the same condition
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM core_user WHERE deleted_at IS NULL"
            )
            raw_count = cursor.fetchone()[0]
        
        # Should match the ORM count
        self.assertEqual(raw_count, User.objects.count())
        
        # Total count should be higher when including soft deleted
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM core_user")
            total_count = cursor.fetchone()[0]
        
        self.assertGreater(total_count, raw_count)
        self.assertEqual(total_count, User.all_objects.count())
    
    def test_soft_delete_field_behavior(self):
        """Test the deleted_at field behavior directly."""
        # Test that deleted_at can be set manually
        test_time = timezone.now()
        self.user.deleted_at = test_time
        self.user.save()
        
        # Verify via DB
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT deleted_at FROM core_user WHERE id = %s",
                [str(self.user.id)]
            )
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], test_time)
        
        # Verify record is excluded from default queryset
        self.assertNotIn(self.user, User.objects.all())
        
        # Test restoring a soft deleted record
        self.user.deleted_at = None
        self.user.save()
        
        # Verify restoration
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT deleted_at FROM core_user WHERE id = %s",
                [str(self.user.id)]
            )
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertIsNone(result[0])
        
        # Verify record is back in default queryset
        self.assertIn(self.user, User.objects.all())


class TestSoftDeleteEdgeCases(TestCase):
    """Test edge cases and error conditions for soft delete."""
    
    def test_multiple_soft_deletes(self):
        """Test that calling soft_delete multiple times works correctly."""
        user = UserFactory()
        
        # First soft delete
        user.soft_delete()
        first_deleted_at = user.deleted_at
        
        # Wait a small amount and soft delete again
        import time
        time.sleep(0.01)
        user.soft_delete()
        second_deleted_at = user.deleted_at
        
        # Should update the timestamp
        self.assertGreater(second_deleted_at, first_deleted_at)
        
        # Should still be excluded from default queryset
        self.assertNotIn(user, User.objects.all())
        self.assertEqual(User.objects.filter(id=user.id).count(), 0)
    
    def test_filter_by_soft_delete_status(self):
        """Test filtering records by their soft delete status."""
        # Create test data
        active_user = UserFactory()
        deleted_user = UserFactory()
        deleted_user.soft_delete()
        
        # Test filtering active records explicitly
        active_users = User.objects.filter(deleted_at__isnull=True)
        self.assertIn(active_user, active_users)
        self.assertNotIn(deleted_user, active_users)
        
        # Test filtering deleted records explicitly
        deleted_users = User.objects.deleted_only()
        self.assertNotIn(active_user, deleted_users)
        self.assertIn(deleted_user, deleted_users)
    
    def test_related_objects_with_soft_delete(self):
        """Test behavior of related objects when parent is soft deleted."""
        # Create organization with project
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)
        
        # Soft delete organization
        org.soft_delete()
        
        # Project should still exist (soft delete doesn't cascade)
        self.assertEqual(Project.objects.count(), 1)
        self.assertIn(project, Project.objects.all())
        
        # But organization should be excluded
        self.assertEqual(Organization.objects.count(), 0)
        
        # Project's organization reference should still work via all_objects
        project.refresh_from_db()
        self.assertEqual(project.organization, org)
        self.assertIn(org, Organization.all_objects.all())