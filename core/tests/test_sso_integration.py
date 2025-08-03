"""
Tests for SSO integration via django-allauth.

This module tests the integration of django-allauth for social and email-based
authentication, including custom adapters and organization scoping.
"""

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import RequestFactory, TestCase
from django.urls import reverse

from core.adapters import CustomAccountAdapter, CustomSocialAccountAdapter
from core.factories import UserFactory

User = get_user_model()


class TestAllauthConfiguration(TestCase):
    """Test basic allauth configuration and setup."""

    def test_allauth_installed_and_configured(self):
        """Test that allauth is properly installed and configured."""
        # Check that allauth is in INSTALLED_APPS
        from django.conf import settings

        self.assertIn("allauth", settings.INSTALLED_APPS)
        self.assertIn("allauth.account", settings.INSTALLED_APPS)
        self.assertIn("allauth.socialaccount", settings.INSTALLED_APPS)
        self.assertIn("allauth.socialaccount.providers.google", settings.INSTALLED_APPS)
        self.assertIn(
            "allauth.socialaccount.providers.microsoft", settings.INSTALLED_APPS
        )

    def test_authentication_backends_configured(self):
        """Test that authentication backends include allauth."""
        from django.conf import settings

        backends = settings.AUTHENTICATION_BACKENDS
        self.assertIn("allauth.account.auth_backends.AuthenticationBackend", backends)
        self.assertIn("django.contrib.auth.backends.ModelBackend", backends)

    def test_allauth_settings_configured(self):
        """Test that allauth settings are properly configured."""
        from django.conf import settings

        # Check account settings
        self.assertEqual(settings.ACCOUNT_LOGIN_METHODS, {"email"})
        self.assertEqual(
            settings.ACCOUNT_SIGNUP_FIELDS, ["email*", "password1*", "password2*"]
        )
        self.assertEqual(settings.ACCOUNT_USER_MODEL_EMAIL_FIELD, "email")
        self.assertIsNone(settings.ACCOUNT_USER_MODEL_USERNAME_FIELD)

        # Check social account settings
        self.assertTrue(settings.SOCIALACCOUNT_EMAIL_REQUIRED)
        self.assertEqual(settings.SOCIALACCOUNT_EMAIL_VERIFICATION, "none")
        self.assertTrue(settings.SOCIALACCOUNT_AUTO_SIGNUP)

    def test_custom_adapters_configured(self):
        """Test that custom adapters are configured."""
        from django.conf import settings

        self.assertEqual(settings.ACCOUNT_ADAPTER, "core.adapters.CustomAccountAdapter")
        self.assertEqual(
            settings.SOCIALACCOUNT_ADAPTER, "core.adapters.CustomSocialAccountAdapter"
        )


class TestAllauthURLs(TestCase):
    """Test that allauth URLs are properly configured."""

    def test_account_urls_exist(self):
        """Test that account URLs are accessible."""
        # Test login URL
        login_url = reverse("account_login")
        self.assertEqual(login_url, "/accounts/login/")

        # Test signup URL
        signup_url = reverse("account_signup")
        self.assertEqual(signup_url, "/accounts/signup/")

        # Test logout URL
        logout_url = reverse("account_logout")
        self.assertEqual(logout_url, "/accounts/logout/")

    def test_social_urls_exist(self):
        """Test that social account URLs are accessible."""
        # Test social login URLs exist (these won't work without apps configured)

        # Just check that the URL patterns are loaded
        try:
            from allauth.socialaccount import urls as social_urls

            self.assertTrue(hasattr(social_urls, "urlpatterns"))
        except ImportError:
            self.fail("Social account URLs not properly configured")


class TestCustomAccountAdapter(TestCase):
    """Test the custom account adapter."""

    def setUp(self):
        """Set up test data."""
        self.request_factory = RequestFactory()
        self.adapter = CustomAccountAdapter()

    def test_is_open_for_signup_default(self):
        """Test that signups are open by default."""
        request = self.request_factory.get("/")
        self.assertTrue(self.adapter.is_open_for_signup(request))

    def test_save_user_custom_logic(self):
        """Test custom user saving logic."""
        from allauth.account.forms import SignupForm

        request = self.request_factory.post("/")
        request.LANGUAGE_CODE = "fr"

        # Create a form with test data
        form_data = {
            "email": "test@example.com",
            "password1": "testpassword123",
            "password2": "testpassword123",
        }
        form = SignupForm(form_data)
        self.assertTrue(form.is_valid())

        # Create user instance
        user = User(email="test@example.com", full_name="Test User")

        # Save user with adapter
        saved_user = self.adapter.save_user(request, user, form)

        # Check that custom logic was applied
        self.assertEqual(saved_user.language, "fr")
        self.assertEqual(saved_user.email, "test@example.com")


class TestCustomSocialAccountAdapter(TestCase):
    """Test the custom social account adapter."""

    def setUp(self):
        """Set up test data."""
        self.request_factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()

        # Create a site for social apps
        self.site = Site.objects.get_or_create(
            domain="example.com", defaults={"name": "example.com"}
        )[0]

    def test_is_open_for_signup_default(self):
        """Test that social signups are open by default."""
        request = self.request_factory.get("/")

        # Create a mock social login
        social_account = SocialAccount(
            provider="google", uid="123456789", extra_data={"email": "test@example.com"}
        )

        # Create mock social login object
        social_login = type(
            "MockSocialLogin",
            (),
            {"account": social_account, "user": None, "is_existing": False},
        )()

        self.assertTrue(self.adapter.is_open_for_signup(request, social_login))

    def test_pre_social_login_existing_user(self):
        """Test pre_social_login logic with existing user."""
        # Create existing user
        existing_user = UserFactory(email="test@example.com")

        request = self.request_factory.get("/")

        # Create social account and login
        social_account = SocialAccount(
            provider="google", uid="123456789", extra_data={"email": "test@example.com"}
        )

        social_login = type(
            "MockSocialLogin",
            (),
            {
                "account": social_account,
                "user": None,
                "is_existing": False,
                "connect": lambda self, req, user: setattr(self, "user", user),
            },
        )()

        # Call pre_social_login
        self.adapter.pre_social_login(request, social_login)

        # User should be connected
        self.assertEqual(social_login.user, existing_user)

    def test_save_user_from_social_login(self):
        """Test saving user from social login."""
        request = self.request_factory.post("/")

        # Create social account with rich data
        social_account = SocialAccount(
            provider="google",
            uid="123456789",
            extra_data={
                "email": "social@example.com",
                "name": "Social User",
                "locale": "fr_FR",
            },
        )

        # Create user instance
        user = User(email="social@example.com")

        # Create mock social login
        social_login = type(
            "MockSocialLogin",
            (),
            {"account": social_account, "user": user, "is_existing": False},
        )()

        # Mock save_user from parent - properly handle arguments
        def mock_save_user(self, request, social_login, form=None):
            user = social_login.user
            user.save()
            return user

        # Patch parent save_user method
        original_save_user = CustomSocialAccountAdapter.__bases__[0].save_user
        CustomSocialAccountAdapter.__bases__[0].save_user = mock_save_user

        try:
            saved_user = self.adapter.save_user(request, social_login)

            # Check that custom logic was applied
            self.assertEqual(saved_user.full_name, "Social User")
            self.assertEqual(saved_user.language, "fr")
            self.assertEqual(saved_user.email, "social@example.com")

        finally:
            # Restore original method
            CustomSocialAccountAdapter.__bases__[0].save_user = original_save_user


class TestSocialProviderConfiguration(TestCase):
    """Test social provider configuration."""

    def test_google_provider_configured(self):
        """Test that Google OAuth2 provider is configured."""
        from django.conf import settings

        providers = settings.SOCIALACCOUNT_PROVIDERS
        self.assertIn("google", providers)

        google_config = providers["google"]
        self.assertIn("SCOPE", google_config)
        self.assertIn("profile", google_config["SCOPE"])
        self.assertIn("email", google_config["SCOPE"])
        self.assertTrue(google_config.get("OAUTH_PKCE_ENABLED", False))

    def test_microsoft_provider_configured(self):
        """Test that Microsoft provider is configured."""
        from django.conf import settings

        providers = settings.SOCIALACCOUNT_PROVIDERS
        self.assertIn("microsoft", providers)

        microsoft_config = providers["microsoft"]
        self.assertIn("SCOPE", microsoft_config)
        self.assertIn("User.Read", microsoft_config["SCOPE"])
        self.assertIn("email", microsoft_config["SCOPE"])


@pytest.mark.django_db
class TestSSOIntegration:
    """Integration tests for SSO functionality."""

    def test_user_creation_preserves_email_as_username(self):
        """Test that user creation via allauth preserves email as username."""
        # Create user manually as allauth would
        user = User.objects.create_user(
            email="sso@example.com", full_name="SSO User", password="testpass123"
        )

        # Verify email is used as username
        assert user.email == "sso@example.com"
        assert user.USERNAME_FIELD == "email"
        assert user.get_username() == "sso@example.com"

    def test_email_address_creation(self):
        """Test EmailAddress model integration."""
        user = UserFactory(email="allauth@example.com")

        # Create EmailAddress as allauth would
        email_address = EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )

        assert email_address.email == user.email
        assert email_address.verified
        assert email_address.primary

    def test_social_account_creation(self):
        """Test SocialAccount model integration."""
        user = UserFactory(email="social@example.com")

        # Create SocialAccount as would happen with SSO
        social_account = SocialAccount.objects.create(
            user=user,
            provider="google",
            uid="1234567890",
            extra_data={
                "email": user.email,
                "name": user.full_name,
                "picture": "https://example.com/avatar.jpg",
            },
        )

        assert social_account.user == user
        assert social_account.provider == "google"
        assert social_account.extra_data["email"] == user.email


class TestSSOErrorHandling(TestCase):
    """Test error handling in SSO integration."""

    def setUp(self):
        """Set up test data."""
        self.request_factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()

    def test_authentication_error_handling(self):
        """Test authentication error handling."""
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.test import RequestFactory

        request = RequestFactory().get("/")

        # Add session support for messages
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Add messages support
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        # Test different error scenarios
        error_scenarios = [
            ("access_denied", "Access was denied"),
            ("invalid_request", "Invalid request"),
            ("unknown_error", "Authentication failed"),
        ]

        for error_code, expected_message in error_scenarios:
            with self.subTest(error_code=error_code):
                # This should not raise an exception
                try:
                    self.adapter.authentication_error(
                        request=request, provider_id="google", error=error_code
                    )
                    # Check that a message was added
                    message_list = list(messages)
                    self.assertTrue(len(message_list) > 0)
                except Exception as e:
                    self.fail(f"authentication_error raised {e} for {error_code}")


class TestSSOAdminIntegration(TestCase):
    """Test Django admin integration for SSO."""

    def test_social_app_admin_available(self):
        """Test that SocialApp can be managed via admin."""
        from allauth.socialaccount.models import SocialApp
        from django.contrib import admin

        # Check that SocialApp is registered in admin
        self.assertIn(SocialApp, admin.site._registry)

    def test_social_account_admin_available(self):
        """Test that SocialAccount can be managed via admin."""
        from allauth.socialaccount.models import SocialAccount
        from django.contrib import admin

        # Check that SocialAccount is registered in admin
        self.assertIn(SocialAccount, admin.site._registry)

    @pytest.mark.django_db
    def test_create_social_app_for_google(self):
        """Test creating a SocialApp for Google OAuth2."""
        from allauth.socialaccount.models import SocialApp

        # Create site
        site = Site.objects.get_or_create(
            domain="example.com", defaults={"name": "example.com"}
        )[0]

        # Create Google social app
        google_app = SocialApp.objects.create(
            provider="google",
            name="Google OAuth2",
            client_id="test-client-id.apps.googleusercontent.com",
            secret="test-secret-key",
        )
        google_app.sites.add(site)

        assert google_app.provider == "google"
        assert google_app.client_id == "test-client-id.apps.googleusercontent.com"
        assert site in google_app.sites.all()
