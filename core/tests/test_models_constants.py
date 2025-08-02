from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core.models import Organization, OrganizationMembership
from core.constants import PlanChoices, LanguageChoices

User = get_user_model()


class TestOrganizationWithConstants(TestCase):
    """Test cases for Organization model with constants integration."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            full_name="Test User"
        )

    def test_organization_default_plan(self):
        """Test that organizations have default plan set to FREE."""
        org = Organization.objects.create(
            name="Test Org",
            created_by=self.user
        )
        self.assertEqual(org.plan, PlanChoices.FREE)

    def test_organization_default_language(self):
        """Test that organizations have default language set correctly."""
        org = Organization.objects.create(
            name="Test Org",
            created_by=self.user
        )
        self.assertEqual(org.language, LanguageChoices.ENGLISH)

    def test_organization_plan_choices(self):
        """Test that organization plan field accepts valid choices."""
        org = Organization.objects.create(
            name="Test Org",
            plan=PlanChoices.STANDARD,
            created_by=self.user
        )
        self.assertEqual(org.plan, PlanChoices.STANDARD)

        org.plan = PlanChoices.ENTERPRISE
        org.save()
        self.assertEqual(org.plan, PlanChoices.ENTERPRISE)

    def test_organization_language_choices(self):
        """Test that organization language field accepts valid choices."""
        org = Organization.objects.create(
            name="Test Org",
            language=LanguageChoices.FRENCH,
            created_by=self.user
        )
        self.assertEqual(org.language, LanguageChoices.FRENCH)

    def test_get_plan_limits(self):
        """Test get_plan_limits method."""
        # Test free plan
        org_free = Organization.objects.create(
            name="Free Org",
            plan=PlanChoices.FREE,
            created_by=self.user
        )
        limits = org_free.get_plan_limits()
        self.assertEqual(limits['max_users'], 5)
        self.assertEqual(limits['max_projects'], 10)

        # Test enterprise plan
        org_enterprise = Organization.objects.create(
            name="Enterprise Org",
            plan=PlanChoices.ENTERPRISE,
            created_by=self.user
        )
        limits = org_enterprise.get_plan_limits()
        self.assertIsNone(limits['max_users'])  # Unlimited
        self.assertIsNone(limits['max_projects'])  # Unlimited

    def test_is_premium_plan(self):
        """Test is_premium_plan method."""
        org_free = Organization.objects.create(
            name="Free Org",
            plan=PlanChoices.FREE,
            created_by=self.user
        )
        self.assertFalse(org_free.is_premium_plan())

        org_standard = Organization.objects.create(
            name="Standard Org",
            plan=PlanChoices.STANDARD,
            created_by=self.user
        )
        self.assertTrue(org_standard.is_premium_plan())

    def test_can_add_users(self):
        """Test can_add_users method."""
        org = Organization.objects.create(
            name="Test Org",
            plan=PlanChoices.FREE,
            created_by=self.user
        )
        
        # Create membership for the creator
        OrganizationMembership.objects.create(
            user=self.user,
            organization=org,
            created_by=self.user
        )
        
        # Free plan allows 5 users, we have 1 (creator), so can add 4 more
        self.assertTrue(org.can_add_users(1))
        self.assertTrue(org.can_add_users(4))
        self.assertFalse(org.can_add_users(5))
        
        # Add some memberships
        for i in range(3):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                full_name=f"User {i}"
            )
            OrganizationMembership.objects.create(
                user=user,
                organization=org,
                created_by=self.user
            )
        
        # Now we have 4 users (creator + 3), can add 1 more
        self.assertTrue(org.can_add_users(1))
        self.assertFalse(org.can_add_users(2))

    def test_can_add_users_unlimited(self):
        """Test can_add_users method with unlimited plan."""
        org = Organization.objects.create(
            name="Enterprise Org",
            plan=PlanChoices.ENTERPRISE,
            created_by=self.user
        )
        
        # Enterprise plan is unlimited
        self.assertTrue(org.can_add_users(1))
        self.assertTrue(org.can_add_users(100))
        self.assertTrue(org.can_add_users(1000))


class TestUserWithConstants(TestCase):
    """Test cases for User model with constants integration."""

    def test_user_default_language(self):
        """Test that users have default language set correctly."""
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User"
        )
        self.assertEqual(user.language, LanguageChoices.ENGLISH)

    def test_user_language_choices(self):
        """Test that user language field accepts valid choices."""
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            language=LanguageChoices.FRENCH
        )
        self.assertEqual(user.language, LanguageChoices.FRENCH)

    def test_get_effective_language_user_preference(self):
        """Test get_effective_language when user has language preference."""
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            language=LanguageChoices.FRENCH
        )
        self.assertEqual(user.get_effective_language(), LanguageChoices.FRENCH)

    def test_get_effective_language_org_default(self):
        """Test get_effective_language when using organization default."""
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            language=""  # No user preference
        )
        
        org = Organization.objects.create(
            name="French Org",
            language=LanguageChoices.FRENCH,
            created_by=user
        )
        
        membership = OrganizationMembership.objects.create(
            user=user,
            organization=org,
            is_default=True,
            created_by=user
        )
        
        self.assertEqual(user.get_effective_language(), LanguageChoices.FRENCH)

    def test_get_effective_language_fallback(self):
        """Test get_effective_language fallback to default."""
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            language=""  # No user preference
        )
        
        # No default organization
        self.assertEqual(user.get_effective_language(), LanguageChoices.ENGLISH)


class TestConstantsIntegration(TestCase):
    """Test integration of constants with the overall system."""

    def test_organization_plan_display(self):
        """Test that plan choices display correctly."""
        user = User.objects.create_user(
            email="testuser@example.com",
            full_name="Test User"
        )
        org = Organization.objects.create(
            name="Test Org",
            plan=PlanChoices.STANDARD,
            created_by=user
        )
        
        # Check that we can get the display value
        self.assertEqual(org.get_plan_display(), "Standard")

    def test_language_choice_display(self):
        """Test that language choices display correctly."""
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            language=LanguageChoices.FRENCH
        )
        
        # Check that we can get the display value
        self.assertEqual(user.get_language_display(), "French")

    def test_backwards_compatibility(self):
        """Test that old string values still work where expected."""
        user = User.objects.create_user(
            email="testuser@example.com",
            full_name="Test User"
        )
        
        # Test that we can still pass string values that match the enum
        org = Organization.objects.create(
            name="Test Org",
            plan="free",  # String value
            language="en",  # String value
            created_by=user
        )
        
        self.assertEqual(org.plan, PlanChoices.FREE)
        self.assertEqual(org.language, LanguageChoices.ENGLISH)