"""
Legacy storage module for backward compatibility.

This module maintains backward compatibility with the original GCS storage
implementation while redirecting to the new multi-cloud storage system.
"""

# Import from the new storage system for backward compatibility
from core.storage.gcs import GCSStorage as _GCSStorage, OrganizationScopedGCSStorage as _OrganizationScopedGCSStorage
from core.storage import get_default_storage

# Re-export the original classes for backward compatibility
GCSStorage = _GCSStorage
OrganizationScopedGCSStorage = _OrganizationScopedGCSStorage

# Function to get default storage (used by Django's DEFAULT_FILE_STORAGE setting)
def get_storage():
    """Get the configured default storage backend."""
    return get_default_storage()

# For Django's DEFAULT_FILE_STORAGE setting compatibility
class DefaultStorageWrapper:
    """Wrapper to make get_default_storage compatible with Django's storage setting."""
    
    def __init__(self):
        self._storage = None
    
    def __getattr__(self, name):
        if self._storage is None:
            self._storage = get_default_storage()
        return getattr(self._storage, name)
    
    def __call__(self):
        if self._storage is None:
            self._storage = get_default_storage()
        return self._storage

# Create an instance that can be used as DEFAULT_FILE_STORAGE
default_storage = DefaultStorageWrapper()

# Make the module callable (for DEFAULT_FILE_STORAGE = "core.storage")
def __call__():
    return get_default_storage()