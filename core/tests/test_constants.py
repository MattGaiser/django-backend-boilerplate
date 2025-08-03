from django.test import TestCase

from core.constants import LanguageChoices, PlanChoices


class TestPlanChoices(TestCase):
    """Test cases for PlanChoices enum."""

    def test_plan_choices_values(self):
        """Test that plan choices have correct values."""
        self.assertEqual(PlanChoices.FREE, "free")
        self.assertEqual(PlanChoices.STANDARD, "standard")
        self.assertEqual(PlanChoices.ENTERPRISE, "enterprise")

    def test_plan_choices_labels(self):
        """Test that plan choices have correct labels."""
        self.assertEqual(str(PlanChoices.FREE.label), "Free")
        self.assertEqual(str(PlanChoices.STANDARD.label), "Standard")
        self.assertEqual(str(PlanChoices.ENTERPRISE.label), "Enterprise")

    def test_plan_choices_choices(self):
        """Test that choices tuple is properly formatted."""
        choices = PlanChoices.choices
        expected = [
            ("free", "Free"),
            ("standard", "Standard"),
            ("enterprise", "Enterprise"),
        ]
        self.assertEqual(choices, expected)

    def test_get_plan_limits_free(self):
        """Test plan limits for free plan."""
        limits = PlanChoices.get_plan_limits(PlanChoices.FREE)
        expected = {
            "max_users": 5,
            "max_projects": 10,
            "storage_gb": 1,
            "api_calls_per_month": 1000,
        }
        self.assertEqual(limits, expected)

    def test_get_plan_limits_standard(self):
        """Test plan limits for standard plan."""
        limits = PlanChoices.get_plan_limits(PlanChoices.STANDARD)
        expected = {
            "max_users": 25,
            "max_projects": 100,
            "storage_gb": 50,
            "api_calls_per_month": 10000,
        }
        self.assertEqual(limits, expected)

    def test_get_plan_limits_enterprise(self):
        """Test plan limits for enterprise plan."""
        limits = PlanChoices.get_plan_limits(PlanChoices.ENTERPRISE)
        expected = {
            "max_users": None,
            "max_projects": None,
            "storage_gb": 500,
            "api_calls_per_month": 100000,
        }
        self.assertEqual(limits, expected)

    def test_get_plan_limits_invalid(self):
        """Test plan limits for invalid plan returns free plan limits."""
        limits = PlanChoices.get_plan_limits("invalid")
        free_limits = PlanChoices.get_plan_limits(PlanChoices.FREE)
        self.assertEqual(limits, free_limits)

    def test_is_premium_plan(self):
        """Test premium plan detection."""
        self.assertFalse(PlanChoices.is_premium_plan(PlanChoices.FREE))
        self.assertTrue(PlanChoices.is_premium_plan(PlanChoices.STANDARD))
        self.assertTrue(PlanChoices.is_premium_plan(PlanChoices.ENTERPRISE))
        self.assertFalse(PlanChoices.is_premium_plan("invalid"))


class TestLanguageChoices(TestCase):
    """Test cases for LanguageChoices enum."""

    def test_language_choices_values(self):
        """Test that language choices have correct values."""
        self.assertEqual(LanguageChoices.ENGLISH, "en")
        self.assertEqual(LanguageChoices.FRENCH, "fr")

    def test_language_choices_labels(self):
        """Test that language choices have correct labels."""
        self.assertEqual(str(LanguageChoices.ENGLISH.label), "English")
        self.assertEqual(str(LanguageChoices.FRENCH.label), "French")

    def test_language_choices_choices(self):
        """Test that choices tuple is properly formatted."""
        choices = LanguageChoices.choices
        expected = [
            ("en", "English"),
            ("fr", "French"),
        ]
        self.assertEqual(choices, expected)

    def test_get_default_language(self):
        """Test default language is English."""
        default = LanguageChoices.get_default_language()
        self.assertEqual(default, LanguageChoices.ENGLISH)

    def test_get_language_name(self):
        """Test getting language display names."""
        self.assertEqual(LanguageChoices.get_language_name("en"), "English")
        self.assertEqual(LanguageChoices.get_language_name("fr"), "French")

    def test_get_language_name_invalid(self):
        """Test getting language name for invalid code returns English."""
        name = LanguageChoices.get_language_name("invalid")
        self.assertEqual(name, "English")

    def test_is_rtl_language(self):
        """Test RTL language detection."""
        self.assertFalse(LanguageChoices.is_rtl_language(LanguageChoices.ENGLISH))
        self.assertFalse(LanguageChoices.is_rtl_language(LanguageChoices.FRENCH))
        self.assertFalse(LanguageChoices.is_rtl_language("invalid"))

    def test_enum_membership(self):
        """Test enum membership checking."""
        # Test using the enum values
        all_languages = [choice[0] for choice in LanguageChoices.choices]
        self.assertIn("en", all_languages)
        self.assertIn("fr", all_languages)
        self.assertNotIn("es", all_languages)
