"""
Google Cloud Storage backend with RBAC support for Django.

This module provides a Django storage backend that integrates with Google Cloud Storage
while enforcing Role-Based Access Control (RBAC) at the organization level.
"""

import os
import logging
from typing import Optional, Union, Dict, Any
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.storage import Storage
from django.core.exceptions import SuspiciousOperation, PermissionDenied
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)


@deconstructible
class GCSStorage(Storage):
    """
    Google Cloud Storage backend with RBAC enforcement.
    
    This storage backend provides organization-scoped file storage with proper
    access control based on the current user's organization membership.
    """

    def __init__(self, bucket_name=None, client_options=None):
        """
        Initialize GCS storage backend.
        
        Args:
            bucket_name: GCS bucket name. Defaults to settings.GCS_BUCKET_NAME
            client_options: Additional options for GCS client
        """
        self.bucket_name = bucket_name or getattr(settings, 'GCS_BUCKET_NAME', 'dev-app-assets')
        self.client_options = client_options or getattr(settings, 'GCS_CLIENT_OPTIONS', {})
        self.use_emulator = getattr(settings, 'USE_GCS_EMULATOR', False)
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Lazy initialization of GCS client."""
        if self._client is None:
            try:
                # Import here to avoid ImportError if google-cloud-storage is not installed
                from google.cloud import storage
                
                if self.use_emulator:
                    # For emulator, create client without authentication
                    self._client = storage.Client.create_anonymous_client()
                    if self.client_options.get('api_endpoint'):
                        self._client._http.base_url = self.client_options['api_endpoint']
                else:
                    # For production, use default authentication
                    self._client = storage.Client(**self.client_options)
                    
            except ImportError:
                logger.error("google-cloud-storage is required but not installed")
                raise ImportError(
                    "google-cloud-storage is required for GCS storage backend. "
                    "Install it with: pip install google-cloud-storage"
                )
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")
                raise

        return self._client

    @property
    def bucket(self):
        """Lazy initialization of GCS bucket."""
        if self._bucket is None:
            try:
                self._bucket = self.client.bucket(self.bucket_name)
                
                # Create bucket if using emulator and it doesn't exist
                if self.use_emulator:
                    try:
                        if not self._bucket.exists():
                            self._bucket.create()
                            logger.info(f"Created emulator bucket: {self.bucket_name}")
                    except Exception as e:
                        logger.warning(f"Could not create emulator bucket: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to initialize GCS bucket {self.bucket_name}: {e}")
                raise

        return self._bucket

    def _get_organization_prefix(self, organization_id: str) -> str:
        """
        Get the storage prefix for an organization.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            Organization-specific prefix for file paths
        """
        return f"orgs/{organization_id}/"

    def _validate_organization_access(self, name: str, organization_id: str) -> str:
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
        # Validate file path for security
        if '..' in name or name.startswith('/'):
            raise SuspiciousOperation(f"Suspicious file path: {name}")

        org_prefix = self._get_organization_prefix(organization_id)
        
        # If path doesn't start with org prefix, add it
        if not name.startswith(org_prefix):
            name = org_prefix + name.lstrip('/')
            
        # Double-check that the path is within the organization scope
        if not name.startswith(org_prefix):
            raise PermissionDenied(f"File access denied: {name} not in organization scope")
            
        return name

    def _open(self, name: str, mode: str = 'rb'):
        """
        Open a file from GCS.
        
        Args:
            name: File path
            mode: File open mode
            
        Returns:
            File-like object
        """
        try:
            blob = self.bucket.blob(name)
            return blob.open(mode)
        except Exception as e:
            logger.error(f"Failed to open file {name}: {e}")
            raise

    def _save(self, name: str, content) -> str:
        """
        Save a file to GCS.
        
        Args:
            name: File path
            content: File content
            
        Returns:
            Final file path
        """
        try:
            blob = self.bucket.blob(name)
            
            # Set content type if available
            if hasattr(content, 'content_type'):
                blob.content_type = content.content_type
            
            # Upload the file
            blob.upload_from_file(content, rewind=True)
            
            logger.info(f"Successfully saved file: {name}")
            return name
            
        except Exception as e:
            logger.error(f"Failed to save file {name}: {e}")
            raise

    def delete(self, name: str) -> None:
        """
        Delete a file from GCS.
        
        Args:
            name: File path to delete
        """
        try:
            blob = self.bucket.blob(name)
            blob.delete()
            logger.info(f"Successfully deleted file: {name}")
        except Exception as e:
            logger.error(f"Failed to delete file {name}: {e}")
            raise

    def exists(self, name: str) -> bool:
        """
        Check if a file exists in GCS.
        
        Args:
            name: File path
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            blob = self.bucket.blob(name)
            return blob.exists()
        except Exception as e:
            logger.error(f"Failed to check if file exists {name}: {e}")
            return False

    def listdir(self, path: str) -> tuple:
        """
        List contents of a directory in GCS.
        
        Args:
            path: Directory path
            
        Returns:
            Tuple of (directories, files)
        """
        if not path.endswith('/'):
            path += '/'
            
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=path, delimiter='/')
            
            files = []
            dirs = []
            
            for blob in blobs:
                if blob.name != path:  # Skip the directory itself
                    files.append(blob.name[len(path):])
            
            # Get prefixes (subdirectories)
            dirs = [prefix[len(path):-1] for prefix in blobs.prefixes or []]
            
            return dirs, files
            
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            return [], []

    def size(self, name: str) -> int:
        """
        Get size of a file in GCS.
        
        Args:
            name: File path
            
        Returns:
            File size in bytes
        """
        try:
            blob = self.bucket.blob(name)
            blob.reload()
            return blob.size or 0
        except Exception as e:
            logger.error(f"Failed to get size of file {name}: {e}")
            return 0

    def url(self, name: str, expire: int = 3600) -> str:
        """
        Get a signed URL for a file.
        
        Args:
            name: File path
            expire: URL expiration time in seconds
            
        Returns:
            Signed URL for the file
        """
        try:
            if self.use_emulator:
                # For emulator, return a simple HTTP URL
                base_url = self.client_options.get('api_endpoint', 'http://localhost:9090')
                return f"{base_url}/storage/v1/b/{self.bucket_name}/o/{name.replace('/', '%2F')}?alt=media"
            else:
                # For production, generate signed URL
                blob = self.bucket.blob(name)
                return blob.generate_signed_url(expiration=expire)
                
        except Exception as e:
            logger.error(f"Failed to generate URL for file {name}: {e}")
            raise

    def get_accessed_time(self, name: str):
        """Not supported by GCS."""
        raise NotImplementedError("GCS doesn't support accessed time")

    def get_created_time(self, name: str):
        """Get creation time of a file."""
        try:
            blob = self.bucket.blob(name)
            blob.reload()
            return blob.time_created
        except Exception:
            return None

    def get_modified_time(self, name: str):
        """Get modification time of a file."""
        try:
            blob = self.bucket.blob(name)
            blob.reload()
            return blob.updated
        except Exception:
            return None


class OrganizationScopedGCSStorage(GCSStorage):
    """
    Organization-scoped GCS storage that enforces RBAC.
    
    This storage automatically scopes all file operations to the current
    organization and validates access permissions.
    """

    def __init__(self, organization_id: str = None, **kwargs):
        """
        Initialize organization-scoped storage.
        
        Args:
            organization_id: Organization UUID to scope storage to
            **kwargs: Additional arguments for parent class
        """
        super().__init__(**kwargs)
        self.organization_id = organization_id

    def _get_current_organization_id(self) -> Optional[str]:
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
        
        return self.organization_id

    def _get_scoped_name(self, name: str) -> str:
        """
        Get organization-scoped file name.
        
        Args:
            name: Original file name
            
        Returns:
            Organization-scoped file name
            
        Raises:
            PermissionDenied: If no organization context is available
        """
        org_id = self._get_current_organization_id()
        if not org_id:
            raise PermissionDenied("No organization context available for file operation")
            
        return self._validate_organization_access(name, org_id)

    def _save(self, name: str, content) -> str:
        """Save file with organization scoping."""
        scoped_name = self._get_scoped_name(name)
        return super()._save(scoped_name, content)

    def _open(self, name: str, mode: str = 'rb'):
        """Open file with organization scoping."""
        scoped_name = self._get_scoped_name(name)
        return super()._open(scoped_name, mode)

    def delete(self, name: str) -> None:
        """Delete file with organization scoping."""
        scoped_name = self._get_scoped_name(name)
        return super().delete(scoped_name)

    def exists(self, name: str) -> bool:
        """Check file existence with organization scoping."""
        scoped_name = self._get_scoped_name(name)
        return super().exists(scoped_name)

    def size(self, name: str) -> int:
        """Get file size with organization scoping."""
        scoped_name = self._get_scoped_name(name)
        return super().size(scoped_name)

    def url(self, name: str, expire: int = 3600) -> str:
        """Get file URL with organization scoping."""
        scoped_name = self._get_scoped_name(name)
        return super().url(scoped_name, expire)

    def listdir(self, path: str) -> tuple:
        """List directory with organization scoping."""
        scoped_path = self._get_scoped_name(path)
        return super().listdir(scoped_path)