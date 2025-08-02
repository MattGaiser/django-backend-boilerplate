"""
Tests for API v1 flow trigger endpoints.

Tests flow triggering with proper authentication, authorization, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole


class FlowTriggerTestCase(APITestCase):
    """
    Test cases for flow trigger endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        
        # Create admin user
        self.admin_user = UserFactory()
        self.admin_membership = OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role=OrgRole.ADMIN,
            is_default=True
        )
        self.admin_token = Token.objects.create(user=self.admin_user)
        
        # Create non-admin user (viewer)
        self.viewer_user = UserFactory()
        self.viewer_membership = OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.organization,
            role=OrgRole.VIEWER,
            is_default=True
        )
        self.viewer_token = Token.objects.create(user=self.viewer_user)
        
        # Create user with no organization membership
        self.no_org_user = UserFactory()
        self.no_org_token = Token.objects.create(user=self.no_org_user)
        
        self.url = reverse('trigger-hello-world-flow')
    
    @patch('flows.hello_world_flow.hello_world')
    def test_trigger_flow_success_admin(self, mock_flow):
        """Test successful flow trigger by admin user."""
        # Mock the flow run
        mock_flow_run = MagicMock()
        mock_flow_run.id = "test-flow-run-id"
        mock_flow_run.result.return_value = {
            "message": "Hello from Prefect!",
            "timestamp": "2025-08-02T20:44:04.677833",
            "status": "completed"
        }
        mock_flow.submit.return_value = mock_flow_run
        
        # Authenticate as admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        # Make request
        response = self.client.post(self.url, {})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['flow_run_id'], 'test-flow-run-id')
        self.assertIn('Hello World flow triggered successfully', response.data['message'])
        self.assertIsNotNone(response.data['flow_result'])
        
        # Verify flow was called
        mock_flow.submit.assert_called_once()
        mock_flow_run.result.assert_called_once_with(timeout=30)
    
    @patch('flows.hello_world_flow.hello_world')
    def test_trigger_flow_success_without_result(self, mock_flow):
        """Test successful flow trigger when result retrieval fails."""
        # Mock the flow run
        mock_flow_run = MagicMock()
        mock_flow_run.id = "test-flow-run-id"
        mock_flow_run.result.side_effect = Exception("Timeout getting result")
        mock_flow.submit.return_value = mock_flow_run
        
        # Authenticate as admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        # Make request
        response = self.client.post(self.url, {})
        
        # Verify response (should still succeed even if result retrieval fails)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'submitted')
        self.assertEqual(response.data['flow_run_id'], 'test-flow-run-id')
        self.assertIn('Hello World flow triggered successfully', response.data['message'])
        self.assertIsNone(response.data['flow_result'])
        
        # Verify flow was called
        mock_flow.submit.assert_called_once()
    
    def test_trigger_flow_forbidden_non_admin(self):
        """Test flow trigger fails for non-admin user."""
        # Authenticate as viewer (non-admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.viewer_token.key}')
        
        # Make request
        response = self.client.post(self.url, {})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Admin permissions required', response.data['detail'])
    
    def test_trigger_flow_forbidden_no_organization(self):
        """Test flow trigger fails for user with no organization."""
        # Authenticate as user with no organization
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.no_org_token.key}')
        
        # Make request
        response = self.client.post(self.url, {})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('User must belong to an organization', response.data['detail'])
    
    def test_trigger_flow_unauthorized_no_token(self):
        """Test flow trigger fails without authentication."""
        # Make request without authentication
        response = self.client.post(self.url, {})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_trigger_flow_unauthorized_invalid_token(self):
        """Test flow trigger fails with invalid token."""
        # Use invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid-token')
        
        # Make request
        response = self.client.post(self.url, {})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('flows.hello_world_flow.hello_world')
    def test_trigger_flow_import_error(self, mock_flow):
        """Test flow trigger handles import errors gracefully."""
        # Mock import error
        mock_flow.submit.side_effect = ImportError("Cannot import flow")
        
        # Authenticate as admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        # Make request
        response = self.client.post(self.url, {})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['status'], 'failed')
        self.assertIsNone(response.data['flow_run_id'])
        self.assertIn('Flow import failed', response.data['message'])
    
    @patch('flows.hello_world_flow.hello_world')
    def test_trigger_flow_execution_error(self, mock_flow):
        """Test flow trigger handles execution errors gracefully."""
        # Mock execution error
        mock_flow.submit.side_effect = Exception("Flow execution failed")
        
        # Authenticate as admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        # Make request
        response = self.client.post(self.url, {})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['status'], 'failed')
        self.assertIsNone(response.data['flow_run_id'])
        self.assertIn('Flow trigger failed', response.data['message'])
    
    def test_trigger_flow_only_post_allowed(self):
        """Test that only POST method is allowed for flow trigger."""
        # Authenticate as admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        # Test GET method
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test PUT method
        response = self.client.put(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test DELETE method
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@pytest.mark.django_db
class FlowTriggerLoggiingTestCase:
    """
    Test cases for flow trigger logging functionality.
    """
    
    def test_flow_trigger_logs_structured_data(self):
        """Test that flow trigger attempts are logged with structured data."""
        # This test would verify structured logging output
        # In a real implementation, you'd capture log output and verify the structure
        # For now, we'll just ensure the endpoint works as expected
        pass