"""
Tests for API v1 authentication endpoints.

Tests token-based authentication, user login/logout, and permission enforcement.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from constants.roles import OrgRole
from core.factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
    UserFactory,
)


class AuthenticationTestCase(APITestCase):
    """
    Test cases for authentication endpoints.
    """

    def setUp(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.user = UserFactory()
        self.membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.organization,
            role=OrgRole.ADMIN,
            is_default=True,
        )
        self.user_password = "testpass123"
        self.user.set_password(self.user_password)
        self.user.save()

    def test_obtain_auth_token_success(self):
        """Test successful token acquisition."""
        url = reverse("api-token-auth")
        data = {"email": self.user.email, "password": self.user_password}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("key", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user.email)

        # Verify token was created
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_obtain_auth_token_invalid_credentials(self):
        """Test token acquisition with invalid credentials."""
        url = reverse("api-token-auth")
        data = {"email": self.user.email, "password": "wrongpassword"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("key", response.data)

    def test_obtain_auth_token_inactive_user(self):
        """Test token acquisition for inactive user."""
        self.user.is_active = False
        self.user.save()

        url = reverse("api-token-auth")
        data = {"email": self.user.email, "password": self.user_password}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revoke_auth_token_success(self):
        """Test successful token revocation."""
        # Create a token for the user
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        url = reverse("api-token-revoke")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify token was deleted
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_revoke_auth_token_no_token(self):
        """Test token revocation when no token exists."""
        # Authenticate user without creating a token
        self.client.force_authenticate(user=self.user)

        url = reverse("api-token-revoke")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_refresh_auth_token_success(self):
        """Test successful token refresh."""
        # Create initial token
        old_token = Token.objects.create(user=self.user)
        old_key = old_token.key
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {old_key}")

        url = reverse("api-token-refresh")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("key", response.data)
        self.assertNotEqual(response.data["key"], old_key)

        # Verify old token is gone and new token exists
        self.assertFalse(Token.objects.filter(key=old_key).exists())
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_token_info_success(self):
        """Test token info endpoint."""
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        url = reverse("api-token-info")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["key"], token.key)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user.email)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        protected_urls = [
            reverse("api-token-revoke"),
            reverse("api-token-refresh"),
            reverse("api-token-info"),
        ]

        for url in protected_urls:
            response = self.client.post(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"URL {url} should require authentication",
            )

    def test_auth_status_authenticated_user(self):
        """Test auth status endpoint with authenticated user."""
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        url = reverse("api-auth-status")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["authenticated"])
        self.assertIsNotNone(response.data["user"])
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertIn("organizations", response.data["user"])

    def test_auth_status_unauthenticated_user(self):
        """Test auth status endpoint with unauthenticated user."""
        url = reverse("api-auth-status")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["authenticated"])
        self.assertIsNone(response.data["user"])

    def test_auth_status_allows_anonymous_access(self):
        """Test that auth status endpoint allows anonymous access."""
        url = reverse("api-auth-status")

        # Test without any authentication
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["authenticated"])

        # Note: Testing with invalid token will return 401 due to DRF authentication
        # middleware, which is the expected behavior. The endpoint allows anonymous
        # access, but if a token is provided, it must be valid.
