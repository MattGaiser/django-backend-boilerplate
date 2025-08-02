"""
Utility functions for the core application.

This module provides helper functions that can be used across the application.
"""


def is_experimental_enabled(user) -> bool:
    """
    Check if experimental features are enabled for a user.
    
    This function checks both superuser override and organization-level flags
    to determine if experimental features should be enabled for the given user.
    
    Args:
        user: User instance to check experimental access for
        
    Returns:
        bool: True if experimental features are enabled, False otherwise
        
    Logic:
        - If user is superuser and has user override enabled, return True
        - Otherwise, return the organization's experimental flag
        - If user has no default organization, return False
    """
    # Superuser override takes precedence
    if user.is_superuser and user.is_experimental_user_override:
        return True
    
    # Check default organization's experimental flag
    default_org = user.get_default_organization()
    if default_org:
        return default_org.is_experimental
    
    # Default to False if no organization
    return False