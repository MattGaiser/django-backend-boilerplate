from django.db import models
from django.test import TestCase

from core.models import BaseModel


class TestPIIValidationIntegration(TestCase):
    """Integration test for PII validation signal."""

    def test_model_without_pii_fields_works(self):
        """Test that models without PII fields work normally."""

        class SimpleModel(BaseModel):
            pii_fields = []  # Explicitly empty
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "core"

        # This should work fine
        self.assertEqual(SimpleModel.pii_fields, [])

    def test_model_with_proper_pii_declaration_works(self):
        """Test that models with proper PII declaration work."""

        class CustomerModel(BaseModel):
            pii_fields = ["email", "full_name"]  # Properly declared
            email = models.EmailField()
            full_name = models.CharField(max_length=100)

            class Meta:
                app_label = "core"

        # This should work fine
        self.assertEqual(set(CustomerModel.pii_fields), {"email", "full_name"})

    def test_integration_with_user_model(self):
        """Test that our User model passes PII validation."""
        from core.models import User

        # User model should have properly declared PII fields
        self.assertTrue(hasattr(User, "pii_fields"))
        expected_pii = {"email", "full_name", "last_login_ip"}
        self.assertEqual(set(User.pii_fields), expected_pii)

    def test_integration_with_organization_model(self):
        """Test that Organization model has proper PII declaration."""
        from core.models import Organization

        # Organization model should declare 'name' as PII
        self.assertTrue(hasattr(Organization, "pii_fields"))
        self.assertIn("name", Organization.pii_fields)

    def test_integration_with_project_model(self):
        """Test that Project model has proper PII declaration."""
        from core.models import Project

        # Project model should declare 'title' as PII
        self.assertTrue(hasattr(Project, "pii_fields"))
        self.assertIn("title", Project.pii_fields)

    def test_integration_with_tag_model(self):
        """Test that Tag model has proper PII declaration."""
        from core.models import Tag

        # Tag model should declare 'title' as PII
        self.assertTrue(hasattr(Tag, "pii_fields"))
        self.assertIn("title", Tag.pii_fields)
