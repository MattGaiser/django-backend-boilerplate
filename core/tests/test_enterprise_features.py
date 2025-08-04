"""
Tests for enterprise features.

Test the new enterprise features to ensure they work correctly.
"""

import json
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.cache import cache_result, cache_key_for_org, get_cache_stats
from core.factories import OrganizationFactory, UserFactory
from core.validation import EnvironmentValidator
from core.webhooks import WebhookEvent, send_user_webhook


class TestEnhancedHealthChecks(TestCase):
    """Test enhanced health check endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_comprehensive_health_check(self):
        """Test the comprehensive health check endpoint."""
        url = reverse("api-health-check")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check response structure
        self.assertIn("status", data)
        self.assertIn("timestamp", data)
        self.assertIn("environment", data)
        self.assertIn("checks", data)
        self.assertIn("metrics", data)
        
        # Check individual checks
        checks = data["checks"]
        self.assertIn("database", checks)
        self.assertIn("cache", checks)
        self.assertIn("django", checks)
        self.assertIn("storage", checks)
    
    def test_liveness_probe(self):
        """Test Kubernetes liveness probe endpoint."""
        url = reverse("api-liveness-probe")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data["status"], "alive")
        self.assertIn("timestamp", data)
    
    def test_readiness_probe(self):
        """Test Kubernetes readiness probe endpoint."""
        url = reverse("api-readiness-probe")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data["status"], "ready")
        self.assertIn("timestamp", data)
        self.assertIn("database", data)


class TestMetricsEndpoints(TestCase):
    """Test metrics and monitoring endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = UserFactory()
        self.org = OrganizationFactory()
    
    def test_application_metrics(self):
        """Test application metrics endpoint."""
        url = reverse("api-metrics")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn("metrics", data)
        self.assertIn("timestamp", data)
        
        metrics = data["metrics"]
        self.assertIn("total_users", metrics)
        self.assertIn("total_organizations", metrics)
        self.assertIn("collection_time_ms", metrics)
    
    def test_prometheus_metrics(self):
        """Test Prometheus-format metrics endpoint."""
        url = reverse("api-prometheus-metrics")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["content-type"], "text/plain; version=0.0.4; charset=utf-8")
        
        content = response.content.decode()
        self.assertIn("django_users_total", content)
        self.assertIn("django_organizations_total", content)
    
    def test_system_status(self):
        """Test system status endpoint."""
        url = reverse("api-system-status")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn("system", data)
        self.assertIn("database", data)
        self.assertIn("cache", data)
        self.assertIn("application", data)


@pytest.mark.django_db
class TestCacheUtilities:
    """Test caching utilities and decorators."""
    
    def test_cache_result_decorator(self):
        """Test cache_result decorator."""
        call_count = 0
        
        @cache_result(timeout=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment
        
        # Different parameters should execute function
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    def test_organization_cache_key(self):
        """Test organization-scoped cache keys."""
        org_id = "test-org-123"
        
        key1 = cache_key_for_org(org_id, "user_stats")
        key2 = cache_key_for_org(org_id, "project_count")
        key3 = cache_key_for_org("other-org", "user_stats")
        
        assert "org" in key1
        assert str(org_id) in key1
        assert "user_stats" in key1
        
        # Different keys for same org
        assert key1 != key2
        
        # Different keys for different orgs
        assert key1 != key3
    
    def test_cache_stats(self):
        """Test cache statistics."""
        stats = get_cache_stats()
        
        assert "backend" in stats
        assert "status" in stats
        assert "operation_time_ms" in stats


class TestEnvironmentValidation(TestCase):
    """Test environment validation utilities."""
    
    def test_environment_validator(self):
        """Test environment validator basic functionality."""
        validator = EnvironmentValidator()
        results = validator.validate_all()
        
        self.assertIn("success", results)
        self.assertIn("errors", results)
        self.assertIn("warnings", results)
        self.assertIn("environment", results)
        
        # Should be a boolean
        self.assertIsInstance(results["success"], bool)
        
        # Should be lists
        self.assertIsInstance(results["errors"], list)
        self.assertIsInstance(results["warnings"], list)
    
    @patch.dict("os.environ", {"SECRET_KEY": "test-secret-key-long-enough-for-validation"})
    def test_secret_key_validation(self):
        """Test secret key validation."""
        validator = EnvironmentValidator()
        validator._validate_security_settings()
        
        # Should not have insecure key error
        insecure_errors = [
            error for error in validator.errors 
            if "django-insecure" in error.lower()
        ]
        self.assertEqual(len(insecure_errors), 0)


class TestWebhookSystem(TestCase):
    """Test webhook system functionality."""
    
    def test_webhook_event_creation(self):
        """Test webhook event creation."""
        event = WebhookEvent(
            event_type="user.created",
            data={"user_id": "123", "email": "test@example.com"},
            user_id="123",
            organization_id="org-456",
            metadata={"source": "api"}
        )
        
        self.assertEqual(event.event_type, "user.created")
        self.assertEqual(event.user_id, "123")
        self.assertEqual(event.organization_id, "org-456")
        self.assertIn("source", event.metadata)
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.timestamp)
    
    def test_webhook_payload_format(self):
        """Test webhook payload format."""
        event = WebhookEvent(
            event_type="organization.updated",
            data={"name": "Test Org"},
            organization_id="org-123"
        )
        
        payload = event.to_payload()
        
        self.assertIn("event_id", payload)
        self.assertIn("event_type", payload)
        self.assertIn("timestamp", payload)
        self.assertIn("data", payload)
        self.assertIn("organization_id", payload)
        
        self.assertEqual(payload["event_type"], "organization.updated")
        self.assertEqual(payload["organization_id"], "org-123")
    
    @patch("core.webhooks.webhook_manager.enabled", False)
    def test_webhook_disabled(self):
        """Test webhook behavior when disabled."""
        user = UserFactory()
        
        # Should return empty list when disabled
        results = send_user_webhook("user.created", user)
        self.assertEqual(results, [])


@pytest.mark.django_db
class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_api_schema_endpoint(self, client):
        """Test API schema endpoint."""
        response = client.get("/api/schema/")
        assert response.status_code == 200
        
        # Should be JSON content
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_swagger_ui_endpoint(self, client):
        """Test Swagger UI endpoint."""
        response = client.get("/api/docs/")
        assert response.status_code == 200
        assert "text/html" in response["content-type"]
    
    def test_redoc_endpoint(self, client):
        """Test ReDoc endpoint."""
        response = client.get("/api/redoc/")
        assert response.status_code == 200
        assert "text/html" in response["content-type"]


class TestEnterpriseFeatureIntegration(TestCase):
    """Integration tests for enterprise features."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = UserFactory()
        self.org = OrganizationFactory()
    
    def test_metrics_include_test_data(self):
        """Test that metrics include our test data."""
        url = reverse("api-metrics")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        metrics = data["metrics"]
        
        # Should include our test user and organization
        self.assertGreaterEqual(metrics["total_users"], 1)
        self.assertGreaterEqual(metrics["total_organizations"], 1)
    
    def test_health_check_reflects_test_environment(self):
        """Test that health checks work in test environment."""
        url = reverse("api-health-check")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should be healthy in test environment
        self.assertEqual(data["status"], "healthy")
        
        # All checks should pass
        checks = data["checks"]
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict):
                self.assertEqual(check_result.get("status"), "healthy", 
                               f"Check {check_name} failed: {check_result}")
    
    def test_cache_functionality_in_tests(self):
        """Test that caching works in test environment."""
        test_key = "test_enterprise_cache_key"
        test_value = {"test": "data", "timestamp": "now"}
        
        # Set cache value
        cache.set(test_key, test_value, timeout=60)
        
        # Retrieve cache value
        cached_value = cache.get(test_key)
        
        self.assertEqual(cached_value, test_value)
        
        # Delete cache value
        cache.delete(test_key)
        
        # Should be None after deletion
        deleted_value = cache.get(test_key)
        self.assertIsNone(deleted_value)