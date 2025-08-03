"""
Tests for base API discovery endpoints.

Tests the base API root endpoint that provides discovery information
for frontend applications.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class APIRootTestCase(APITestCase):
    """
    Test cases for the base API root endpoint.
    """
    
    def test_api_root_accessible_without_authentication(self):
        """Test that API root is accessible without authentication."""
        url = '/api/v1/'  # Updated path since API root is now under v1
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_root_structure(self):
        """Test that API root returns expected structure."""
        url = '/api/v1/'  # Updated path since API root is now under v1
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields are present
        required_fields = ['message', 'versions', 'authentication', 'docs']
        for field in required_fields:
            self.assertIn(field, response.data)
        
        # Check versions structure
        self.assertIn('v1', response.data['versions'])
        self.assertTrue(response.data['versions']['v1'].endswith('/api/v1/'))
        
        # Check authentication endpoints
        auth_endpoints = response.data['authentication']
        required_auth_endpoints = ['login', 'status', 'refresh', 'revoke']
        for endpoint in required_auth_endpoints:
            self.assertIn(endpoint, auth_endpoints)
            self.assertIsInstance(auth_endpoints[endpoint], str)
            self.assertTrue(auth_endpoints[endpoint].startswith('http'))
        
        # Check docs structure
        self.assertIn('version', response.data['docs'])
        self.assertTrue(response.data['docs']['version'].endswith('/api/v1/version/'))
    
    def test_api_root_absolute_urls(self):
        """Test that API root returns absolute URLs."""
        url = '/api/v1/'  # Updated path since API root is now under v1
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # All URLs should be absolute (start with http)
        for version_url in response.data['versions'].values():
            self.assertTrue(version_url.startswith('http'))
        
        for auth_url in response.data['authentication'].values():
            self.assertTrue(auth_url.startswith('http'))
        
        for doc_url in response.data['docs'].values():
            self.assertTrue(doc_url.startswith('http'))
    
    def test_api_root_message(self):
        """Test that API root contains expected message."""
        url = '/api/v1/'  # Updated path since API root is now under v1
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Django Backend Boilerplate API')