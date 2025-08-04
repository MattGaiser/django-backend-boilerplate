"""
Tests for internationalization (i18n) functionality.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import translation

from constants.roles import OrgRole
from core.models import Organization, OrganizationMembership, Project

User = get_user_model()


class InternationalizationTestCase(TestCase):
    """Test internationalization functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", full_name="Test User", password="testpass123"
        )
        self.organization = Organization.objects.create(
            name="Test Organization", description="A test organization"
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization,
            role=OrgRole.ADMIN,
            is_default=True,
        )

    def test_language_setting_defaults(self):
        """Test that language settings are configured correctly."""
        from django.conf import settings

        # Check that USE_I18N is enabled
        self.assertTrue(settings.USE_I18N)
        self.assertTrue(settings.USE_L10N)

        # Check default language
        self.assertEqual(settings.LANGUAGE_CODE, "en")

        # Check that French is in LANGUAGES
        language_codes = [lang[0] for lang in settings.LANGUAGES]
        self.assertIn("en", language_codes)
        self.assertIn("fr", language_codes)

        # Check LOCALE_PATHS is configured
        self.assertTrue(hasattr(settings, "LOCALE_PATHS"))
        self.assertTrue(len(settings.LOCALE_PATHS) > 0)

    def test_model_verbose_names_translations(self):
        """Test that model verbose names support translation."""
        # Test in English (default)
        with translation.override("en"):
            self.assertEqual(str(User._meta.verbose_name), "User")
            self.assertEqual(str(Organization._meta.verbose_name), "Organization")
            self.assertEqual(str(Project._meta.verbose_name), "Project")

    def test_field_help_text_translations(self):
        """Test that field help texts support translation."""
        with translation.override("en"):
            # Get field help text
            email_field = User._meta.get_field("email")
            self.assertIn("Email address", str(email_field.help_text))

            name_field = Organization._meta.get_field("name")
            self.assertIn("Name of the organization", str(name_field.help_text))

    def test_choice_field_translations(self):
        """Test that choice fields support translation."""
        with translation.override("en"):
            # Test OrgRole choices
            admin_choice = OrgRole.ADMIN
            admin_display = dict(OrgRole.choices)[admin_choice]
            self.assertEqual(str(admin_display), "Admin")

            # Test Project status choices
            in_progress_choice = Project.StatusChoices.IN_PROGRESS
            in_progress_display = dict(Project.StatusChoices.choices)[in_progress_choice]
            self.assertEqual(str(in_progress_display), "In Progress")

    def test_language_switching(self):
        """Test that language switching works correctly."""
        # Test switching to French (even though translations aren't filled)
        with translation.override("fr"):
            # The translation should exist but be empty, so should fall back to English
            current_language = translation.get_language()
            self.assertEqual(current_language, "fr")

    def test_user_language_preference(self):
        """Test that user model includes language preference field."""
        user = User.objects.get(email="test@example.com")

        # Test default language
        self.assertEqual(user.language, "en")

        # Test setting French
        user.language = "fr"
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.language, "fr")

    def test_organization_language_preference(self):
        """Test that organization model includes language preference field."""
        org = Organization.objects.get(name="Test Organization")

        # Test default language
        self.assertEqual(org.language, "en")

        # Test setting French
        org.language = "fr"
        org.save()
        org.refresh_from_db()
        self.assertEqual(org.language, "fr")

    def test_user_effective_language(self):
        """Test user's effective language method (user preference or org default)."""
        user = User.objects.get(email="test@example.com")
        org = Organization.objects.get(name="Test Organization")

        # Test with no user preference, no org preference (should default to 'en')
        user.language = ""
        org.language = ""
        user.save()
        org.save()
        self.assertEqual(user.get_effective_language(), "en")

        # Test with org preference but no user preference
        org.language = "fr"
        org.save()
        self.assertEqual(user.get_effective_language(), "fr")

        # Test with user preference (should override org preference)
        user.language = "en"
        user.save()
        self.assertEqual(user.get_effective_language(), "en")

    def test_translation_files_exist(self):
        """Test that translation files have been created."""
        import os

        from django.conf import settings

        # Check that French translation files exist
        locale_path = settings.LOCALE_PATHS[0]
        fr_po_file = os.path.join(locale_path, "fr", "LC_MESSAGES", "django.po")
        fr_mo_file = os.path.join(locale_path, "fr", "LC_MESSAGES", "django.mo")

        self.assertTrue(os.path.exists(fr_po_file), "French .po file should exist")
        self.assertTrue(os.path.exists(fr_mo_file), "French .mo file should exist")

    def test_middleware_configuration(self):
        """Test that LocaleMiddleware is properly configured."""
        from django.conf import settings

        # Check that LocaleMiddleware is in MIDDLEWARE
        self.assertIn("django.middleware.locale.LocaleMiddleware", settings.MIDDLEWARE)

        # Check that it's positioned correctly (after Session, before Common)
        middleware_list = settings.MIDDLEWARE
        locale_index = middleware_list.index(
            "django.middleware.locale.LocaleMiddleware"
        )
        session_index = middleware_list.index(
            "django.contrib.sessions.middleware.SessionMiddleware"
        )
        common_index = middleware_list.index(
            "django.middleware.common.CommonMiddleware"
        )

        self.assertGreater(
            locale_index,
            session_index,
            "LocaleMiddleware should come after SessionMiddleware",
        )
        self.assertLess(
            locale_index,
            common_index,
            "LocaleMiddleware should come before CommonMiddleware",
        )


class UpdateTranslationsCommandTestCase(TestCase):
    """Test the update_translations management command."""

    def test_command_exists(self):
        """Test that the update_translations command exists and can be imported."""
        from django.core.management import get_commands

        commands = get_commands()
        self.assertIn("update_translations", commands)

    def test_command_help(self):
        """Test that the command help works."""
        from django.core.management import call_command

        # This should not raise an exception
        try:
            call_command("update_translations", "--help")
        except SystemExit:
            # --help causes SystemExit, which is expected
            pass
