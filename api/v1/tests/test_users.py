"""
Tests for API v1 user endpoints.

Tests the /me/ endpoint, user profile management, and organization-scoped access.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole


class UserMeEndpointTestCase(APITestCase):
    """
    Test cases for the /me/ endpoint.
    """
    
    def setUp(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.user = UserFactory()
        self.membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.organization,
            role=OrgRole.ADMIN,
            is_default=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_get_me_endpoint_success(self):
        """Test successful retrieval of user profile."""
        url = reverse('users-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['full_name'], self.user.full_name)
        self.assertIn('organizations', response.data)
        self.assertIn('default_organization', response.data)
        
        # Check organization data
        self.assertEqual(len(response.data['organizations']), 1)
        org_data = response.data['organizations'][0]
        self.assertEqual(org_data['organization_name'], self.organization.name)
        self.assertEqual(org_data['role'], OrgRole.ADMIN)
        self.assertTrue(org_data['is_default'])
    
    def test_get_me_endpoint_unauthenticated(self):
        """Test /me/ endpoint without authentication."""
        self.client.credentials()  # Remove authentication
        url = reverse('users-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_patch_me_endpoint_success(self):
        """Test successful update of user profile."""
        url = reverse('users-me')
        data = {
            'full_name': 'Updated Name',
            'language': 'es',
            'timezone': 'America/New_York'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Updated Name')
        self.assertEqual(response.data['language'], 'es')
        self.assertEqual(response.data['timezone'], 'America/New_York')
        
        # Verify database was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')
        self.assertEqual(self.user.language, 'es')
        self.assertEqual(self.user.timezone, 'America/New_York')
    
    def test_patch_me_endpoint_invalid_data(self):
        """Test updating user profile with invalid data."""
        url = reverse('users-me')
        data = {
            'full_name': '',  # Empty name should be invalid
            'language': 'x' * 20  # Too long
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('full_name', response.data)
        self.assertIn('language', response.data)
    
    def test_patch_me_endpoint_readonly_fields(self):
        """Test that read-only fields cannot be updated."""
        url = reverse('users-me')
        original_email = self.user.email
        original_date_joined = self.user.date_joined
        
        data = {
            'email': 'newemail@example.com',
            'date_joined': '2020-01-01T00:00:00Z',
            'is_active': False
        }
        
        response = self.client.patch(url, data)
        
        # Should succeed but ignore read-only fields
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify read-only fields weren't changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, original_email)
        self.assertEqual(self.user.date_joined, original_date_joined)
        self.assertTrue(self.user.is_active)
    
    def test_change_password_success(self):
        """Test successful password change."""
        url = reverse('users-change-password')
        old_password = 'oldpass123'
        new_password = 'newpass456'
        
        # Set a known password
        self.user.set_password(old_password)
        self.user.save()
        
        data = {
            'current_password': old_password,
            'new_password': new_password,
            'new_password_confirm': new_password
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password(old_password))
    
    def test_change_password_wrong_current_password(self):
        """Test password change with wrong current password."""
        url = reverse('users-change-password')
        
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)
    
    def test_change_password_mismatched_confirmation(self):
        """Test password change with mismatched confirmation."""
        url = reverse('users-change-password')
        
        data = {
            'current_password': 'correctpass',
            'new_password': 'newpass456',
            'new_password_confirm': 'differentpass'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password_confirm', response.data)


class UserViewSetTestCase(APITestCase):
    """
    Test cases for the UserViewSet (organization-scoped user management).
    """
    
    def setUp(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.admin_user = UserFactory()
        self.manager_user = UserFactory()
        self.viewer_user = UserFactory()
        self.other_org_user = UserFactory()
        
        # Create memberships
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.organization,
            role=OrgRole.ADMIN,
            is_default=True
        )
        OrganizationMembershipFactory(
            user=self.manager_user,
            organization=self.organization,
            role=OrgRole.MANAGER
        )
        OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.organization,
            role=OrgRole.VIEWER
        )
        
        # User from different organization
        other_org = OrganizationFactory()
        OrganizationMembershipFactory(
            user=self.other_org_user,
            organization=other_org,
            role=OrgRole.ADMIN
        )
    
    def test_admin_can_list_users(self):
        """Test that admin can list users in their organization."""
        token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('users-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see users in the same organization
        user_emails = [user['email'] for user in response.data['results']]
        self.assertIn(self.admin_user.email, user_emails)
        self.assertIn(self.manager_user.email, user_emails)
        self.assertIn(self.viewer_user.email, user_emails)
        self.assertNotIn(self.other_org_user.email, user_emails)
    
    def test_manager_cannot_list_users(self):
        """Test that managers cannot list users (requires admin role)."""
        token = Token.objects.create(user=self.manager_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('users-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_viewer_cannot_list_users(self):
        """Test that viewers cannot list users (requires admin role)."""
        token = Token.objects.create(user=self.viewer_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('users-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_public_users_accessible_to_org_members(self):
        """Test that public user endpoints work for organization members."""
        token = Token.objects.create(user=self.viewer_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('public-users-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see limited user info for org members
        user_emails = [user['full_name'] for user in response.data['results']]
        self.assertIn(self.admin_user.full_name, user_emails)
        self.assertIn(self.manager_user.full_name, user_emails)
        self.assertIn(self.viewer_user.full_name, user_emails)