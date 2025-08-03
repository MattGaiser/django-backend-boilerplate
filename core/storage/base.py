"""
Base storage interface for multi-cloud file storage abstraction.

This module defines abstract interfaces that can be implemented for different
cloud storage providers (GCS, S3, Azure Blob, etc.) to reduce vendor lock-in.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple, List
from django.core.files.storage import Storage


class CloudStorageInterface(ABC):
    """
    Abstract interface for cloud storage operations.
    
    This interface defines the standard operations that all cloud storage
    backends must implement, enabling easy switching between providers.
    """

    @abstractmethod
    def save_file(self, name: str, content, content_type: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Save a file to cloud storage.
        
        Args:
            name: File path/name
            content: File content (file-like object)
            content_type: MIME content type
            metadata: Additional metadata key-value pairs
            
        Returns:
            Final file path
        """
        pass

    @abstractmethod
    def get_file(self, name: str):
        """
        Retrieve a file from cloud storage.
        
        Args:
            name: File path
            
        Returns:
            File-like object
        """
        pass

    @abstractmethod
    def delete_file(self, name: str) -> bool:
        """
        Delete a file from cloud storage.
        
        Args:
            name: File path
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def file_exists(self, name: str) -> bool:
        """
        Check if a file exists in cloud storage.
        
        Args:
            name: File path
            
        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_file_url(self, name: str, expire_seconds: int = 3600) -> str:
        """
        Generate a signed URL for file access.
        
        Args:
            name: File path
            expire_seconds: URL expiration time in seconds
            
        Returns:
            Signed URL for file access
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "", delimiter: str = "/") -> Tuple[List[str], List[str]]:
        """
        List files and directories in cloud storage.
        
        Args:
            prefix: Directory prefix to filter by
            delimiter: Directory delimiter character
            
        Returns:
            Tuple of (directories, files)
        """
        pass

    @abstractmethod
    def get_file_size(self, name: str) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            name: File path
            
        Returns:
            File size in bytes
        """
        pass

    @abstractmethod
    def get_file_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a file.
        
        Args:
            name: File path
            
        Returns:
            Dictionary containing file metadata
        """
        pass


class BaseCloudStorage(Storage, CloudStorageInterface):
    """
    Base Django storage backend that implements both Django Storage
    interface and our cloud storage interface.
    """

    def __init__(self, **kwargs):
        """Initialize storage backend with configuration."""
        super().__init__()
        self.config = kwargs

    def _open(self, name: str, mode: str = 'rb'):
        """Django Storage interface: Open a file."""
        return self.get_file(name)

    def _save(self, name: str, content) -> str:
        """Django Storage interface: Save a file."""
        content_type = getattr(content, 'content_type', None)
        return self.save_file(name, content, content_type)

    def delete(self, name: str) -> None:
        """Django Storage interface: Delete a file."""
        self.delete_file(name)

    def exists(self, name: str) -> bool:
        """Django Storage interface: Check if file exists."""
        return self.file_exists(name)

    def size(self, name: str) -> int:
        """Django Storage interface: Get file size."""
        return self.get_file_size(name)

    def url(self, name: str) -> str:
        """Django Storage interface: Get file URL."""
        return self.get_file_url(name)

    def listdir(self, path: str) -> Tuple[List[str], List[str]]:
        """Django Storage interface: List directory contents."""
        if not path.endswith('/'):
            path += '/'
        return self.list_files(prefix=path)

    def get_accessed_time(self, name: str):
        """Not supported by most cloud providers."""
        raise NotImplementedError("Access time not supported by cloud storage")

    def get_created_time(self, name: str):
        """Get file creation time from metadata."""
        metadata = self.get_file_metadata(name)
        return metadata.get('created_time')

    def get_modified_time(self, name: str):
        """Get file modification time from metadata."""
        metadata = self.get_file_metadata(name)
        return metadata.get('modified_time')


class OrganizationScopedStorageMixin:
    """
    Mixin that adds organization-scoped file operations.
    
    This mixin can be combined with any cloud storage backend to automatically
    scope all operations to the current user's organization.
    """

    def get_organization_prefix(self, organization_id: str) -> str:
        """
        Get the storage prefix for an organization.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            Organization-specific prefix for file paths
        """
        return f"orgs/{organization_id}/"

    def validate_organization_access(self, name: str, organization_id: str) -> str:
        """
        Validate that the file path belongs to the specified organization.
        
        Args:
            name: File path/name
            organization_id: UUID of the organization
            
        Returns:
            Validated file path with organization prefix
            
        Raises:
            PermissionDenied: If path doesn't match organization scope
            SuspiciousOperation: If path contains suspicious characters
        """
        from django.core.exceptions import SuspiciousOperation, PermissionDenied
        
        # Validate file path for security
        if '..' in name or name.startswith('/'):
            raise SuspiciousOperation(f"Suspicious file path: {name}")

        org_prefix = self.get_organization_prefix(organization_id)
        
        # Check if path already has an organization prefix
        if name.startswith("orgs/"):
            # If it has an org prefix but it's not the correct one, deny access
            if not name.startswith(org_prefix):
                raise PermissionDenied(f"File access denied: {name} not in organization scope")
        else:
            # If path doesn't start with org prefix, add it
            name = org_prefix + name.lstrip('/')
            
        # Final validation that the path is within the organization scope
        if not name.startswith(org_prefix):
            raise PermissionDenied(f"File access denied: {name} not in organization scope")
            
        return name

    def get_current_organization_id(self) -> Optional[str]:
        """
        Get the current organization ID from thread-local storage or request context.
        
        Returns:
            Organization ID string or None
        """
        from core.signals import get_current_user
        
        user = get_current_user()
        if user and user.is_authenticated:
            default_org = user.get_default_organization()
            if default_org:
                return str(default_org.id)
        
        return None

    def get_scoped_name(self, name: str) -> str:
        """
        Get organization-scoped file name.
        
        Args:
            name: Original file name
            
        Returns:
            Organization-scoped file name
            
        Raises:
            PermissionDenied: If no organization context is available
        """
        from django.core.exceptions import PermissionDenied
        
        org_id = self.get_current_organization_id()
        if not org_id:
            raise PermissionDenied("No organization context available for file operation")
            
        return self.validate_organization_access(name, org_id)


class CloudStorageFactory:
    """
    Factory class for creating cloud storage backends based on configuration.
    """
    
    _backends = {}
    
    @classmethod
    def register_backend(cls, name: str, backend_class):
        """Register a storage backend."""
        cls._backends[name] = backend_class
    
    @classmethod
    def create_storage(cls, provider: str, **config) -> CloudStorageInterface:
        """
        Create a storage backend instance.
        
        Args:
            provider: Cloud provider name (gcs, s3, azure, etc.)
            **config: Configuration parameters for the backend
            
        Returns:
            Storage backend instance
        """
        if provider not in cls._backends:
            raise ValueError(f"Unknown storage provider: {provider}")
        
        backend_class = cls._backends[provider]
        return backend_class(**config)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available storage providers."""
        return list(cls._backends.keys())