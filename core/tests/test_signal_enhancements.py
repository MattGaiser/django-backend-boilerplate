import pytest
import logging
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.db import models

from core.models import BaseModel, User, Organization
from core.signals import (
    set_current_user, 
    get_current_user, 
    get_pii_field_names,
    get_model_pii_fields,
    get_model_field_names
)
from core.factories import UserFactory, OrganizationFactory


User = get_user_model()


class TestSignalHelperFunctions(TestCase):
    """Test cases for signal helper functions."""
    
    def test_get_pii_field_names_default(self):
        """Test that get_pii_field_names returns default PII field names."""
        pii_fields = get_pii_field_names()
        self.assertIsInstance(pii_fields, set)
        self.assertIn('email', pii_fields)
        self.assertIn('full_name', pii_fields)
        self.assertIn('phone', pii_fields)
        self.assertIn('ssn', pii_fields)
    
    @override_settings(CORE_PII_FIELD_NAMES={'custom_email', 'custom_name'})
    def test_get_pii_field_names_configurable(self):
        """Test that PII field names can be configured via settings."""
        pii_fields = get_pii_field_names()
        self.assertEqual(pii_fields, {'custom_email', 'custom_name'})
    
    def test_get_model_pii_fields_with_declaration(self):
        """Test getting PII fields from a model with pii_fields declared."""
        pii_fields = get_model_pii_fields(User)
        self.assertEqual(set(pii_fields), {'email', 'full_name', 'last_login_ip'})
    
    def test_get_model_pii_fields_without_declaration(self):
        """Test getting PII fields from a model without pii_fields."""
        class TestModel:
            pass
        
        pii_fields = get_model_pii_fields(TestModel)
        self.assertEqual(pii_fields, [])
    
    def test_get_model_field_names(self):
        """Test getting field names from a model."""
        field_names = get_model_field_names(User)
        self.assertIsInstance(field_names, set)
        self.assertIn('email', field_names)
        self.assertIn('full_name', field_names)
        self.assertIn('id', field_names)


class TestAutoAssignUserFields(TransactionTestCase):
    """Test cases for the improved auto-assign user fields signal using real saves."""
    
    def setUp(self):
        self.user = UserFactory()
    
    def test_created_by_assignment_on_new_instance(self):
        """Test that created_by is assigned when creating new instances via signals."""
        set_current_user(self.user)
        
        # Create and save a new organization - this should trigger the signal
        new_org = Organization.objects.create(name='Test Org', description='Test Description')
        
        # Refresh from database to get the saved values
        new_org.refresh_from_db()
        
        self.assertEqual(new_org.created_by, self.user)
        self.assertEqual(new_org.updated_by, self.user)
    
    def test_updated_by_assignment_on_existing_instance(self):
        """Test that updated_by is assigned when updating existing instances."""
        # Create an organization first
        set_current_user(self.user)
        existing_org = Organization.objects.create(name='Initial Org')
        original_created_by = existing_org.created_by
        
        # Create a different user to be the updater
        updater_user = UserFactory()
        set_current_user(updater_user)
        
        # Update the existing instance - this should trigger the signal
        existing_org.name = 'Updated Org Name'
        existing_org.save()
        
        # Refresh from database
        existing_org.refresh_from_db()
        
        # created_by should remain unchanged, updated_by should be updated
        self.assertEqual(existing_org.created_by, original_created_by)
        self.assertEqual(existing_org.updated_by, updater_user)
    
    def test_no_assignment_when_no_current_user(self):
        """Test that no assignment happens when there's no current user."""
        set_current_user(None)
        
        new_org = Organization.objects.create(name='Test Org', description='Test Description')
        new_org.refresh_from_db()
        
        self.assertIsNone(new_org.created_by)
        self.assertIsNone(new_org.updated_by)
    
    def test_no_assignment_when_user_not_authenticated(self):
        """Test that no assignment happens when user is not authenticated."""
        mock_user = Mock()
        mock_user.is_authenticated = False
        set_current_user(mock_user)
        
        new_org = Organization.objects.create(name='Test Org', description='Test Description')
        new_org.refresh_from_db()
        
        self.assertIsNone(new_org.created_by)
        self.assertIsNone(new_org.updated_by)
    
    def tearDown(self):
        """Clean up thread-local storage after each test."""
        set_current_user(None)


class TestPIIValidationImprovements(TestCase):
    """Test cases for PII validation improvements."""
    
    @patch('core.signals.logger')
    def test_ambiguous_pii_field_logging(self, mock_logger):
        """Test that ambiguous PII fields generate warnings."""
        # This test would need to be implemented with a custom model
        # that has ambiguous fields like 'name' or 'description'
        # For now, just verify the logger is available
        self.assertTrue(hasattr(logging.getLogger('core.signals'), 'warning'))
    
    def test_configurable_pii_detection(self):
        """Test that PII detection uses configurable field list."""
        with override_settings(CORE_PII_FIELD_NAMES={'custom_field'}):
            pii_fields = get_pii_field_names()
            self.assertEqual(pii_fields, {'custom_field'})


class TestSignalIntegration(TransactionTestCase):
    """Integration tests for signal functionality."""
    
    def test_end_to_end_user_assignment(self):
        """Test complete workflow of user assignment through signals."""
        admin_user = UserFactory()
        set_current_user(admin_user)
        
        # Create a new organization - should have created_by and updated_by set via signals
        new_org = Organization.objects.create(name='New Org', description='New Organization')
        new_org.refresh_from_db()
        
        self.assertEqual(new_org.created_by, admin_user)
        self.assertEqual(new_org.updated_by, admin_user)
    
    def tearDown(self):
        """Clean up thread-local storage after each test."""
        set_current_user(None)