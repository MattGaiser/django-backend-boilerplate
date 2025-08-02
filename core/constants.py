from django.db import models
from django.utils.translation import gettext_lazy as _


class PlanChoices(models.TextChoices):
    """Enumeration of subscription plan options."""
    FREE = "free", _("Free")
    STANDARD = "standard", _("Standard")
    ENTERPRISE = "enterprise", _("Enterprise")

    @classmethod
    def get_plan_limits(cls, plan):
        """
        Get the limits for a specific plan.
        
        Args:
            plan: Plan choice value
            
        Returns:
            dict: Dictionary containing limits for the plan
        """
        limits = {
            cls.FREE: {
                'max_users': 5,
                'max_projects': 10,
                'storage_gb': 1,
                'api_calls_per_month': 1000,
            },
            cls.STANDARD: {
                'max_users': 25,
                'max_projects': 100,
                'storage_gb': 50,
                'api_calls_per_month': 10000,
            },
            cls.ENTERPRISE: {
                'max_users': None,  # Unlimited
                'max_projects': None,  # Unlimited
                'storage_gb': 500,
                'api_calls_per_month': 100000,
            },
        }
        return limits.get(plan, limits[cls.FREE])

    @classmethod
    def is_premium_plan(cls, plan):
        """
        Check if a plan is a premium (paid) plan.
        
        Args:
            plan: Plan choice value
            
        Returns:
            bool: True if plan is premium, False otherwise
        """
        return plan in [cls.STANDARD, cls.ENTERPRISE]


class LanguageChoices(models.TextChoices):
    """Enumeration of supported language options."""
    ENGLISH = "en", _("English")
    FRENCH = "fr", _("French")

    @classmethod
    def get_default_language(cls):
        """
        Get the default language.
        
        Returns:
            str: Default language code
        """
        return cls.ENGLISH

    @classmethod
    def get_language_name(cls, language_code):
        """
        Get the display name for a language code.
        
        Args:
            language_code: Language choice value
            
        Returns:
            str: Display name of the language
        """
        choice_dict = dict(cls.choices)
        return choice_dict.get(language_code, choice_dict[cls.ENGLISH])

    @classmethod
    def is_rtl_language(cls, language_code):
        """
        Check if a language is right-to-left.
        
        Args:
            language_code: Language choice value
            
        Returns:
            bool: True if language is RTL, False otherwise
        """
        # For now, EN and FR are both LTR languages
        rtl_languages = []
        return language_code in rtl_languages