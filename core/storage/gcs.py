"""
Google Cloud Storage backend implementation using the abstract storage interface.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from django.conf import settings
from .base import BaseCloudStorage, OrganizationScopedStorageMixin, CloudStorageFactory

logger = logging.getLogger(__name__)


class GCSStorage(BaseCloudStorage):
    """
    Google Cloud Storage implementation of the abstract storage interface.
    """

    def __init__(self, bucket_name=None, client_options=None, use_emulator=None, **kwargs):
        """
        Initialize GCS storage backend.
        
        Args:
            bucket_name: GCS bucket name
            client_options: Additional options for GCS client
            use_emulator: Whether to use the GCS emulator
        """
        super().__init__(**kwargs)
        
        # Use provided values or try to get from settings, with sensible defaults
        self.bucket_name = bucket_name
        if self.bucket_name is None:
            try:
                from django.conf import settings
                self.bucket_name = getattr(settings, 'CLOUD_STORAGE_BUCKET_NAME', 'dev-app-assets')
            except:
                self.bucket_name = 'dev-app-assets'
        
        self.client_options = client_options
        if self.client_options is None:
            try:
                from django.conf import settings
                self.client_options = getattr(settings, 'GCS_CLIENT_OPTIONS', {})
            except:
                self.client_options = {}
        
        self.use_emulator = use_emulator
        if self.use_emulator is None:
            try:
                from django.conf import settings
                self.use_emulator = getattr(settings, 'USE_GCS_EMULATOR', False)
            except:
                self.use_emulator = False
        
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Lazy initialization of GCS client."""
        if self._client is None:
            try:
                from google.cloud import storage
                
                if self.use_emulator:
                    self._client = storage.Client.create_anonymous_client()
                    if self.client_options.get('api_endpoint'):
                        self._client._http.base_url = self.client_options['api_endpoint']
                else:
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

    def save_file(self, name: str, content, content_type: str = None, metadata: Dict[str, Any] = None) -> str:
        """Save a file to GCS."""
        try:
            blob = self.bucket.blob(name)
            
            if content_type:
                blob.content_type = content_type
            elif hasattr(content, 'content_type'):
                blob.content_type = content.content_type
            
            if metadata:
                blob.metadata = metadata
            
            blob.upload_from_file(content, rewind=True)
            
            logger.info(f"Successfully saved file: {name}")
            return name
            
        except Exception as e:
            logger.error(f"Failed to save file {name}: {e}")
            raise

    def get_file(self, name: str):
        """Get a file from GCS."""
        try:
            blob = self.bucket.blob(name)
            return blob.open('rb')
        except Exception as e:
            logger.error(f"Failed to open file {name}: {e}")
            raise

    def delete_file(self, name: str) -> bool:
        """Delete a file from GCS."""
        try:
            blob = self.bucket.blob(name)
            blob.delete()
            logger.info(f"Successfully deleted file: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {name}: {e}")
            return False

    def file_exists(self, name: str) -> bool:
        """Check if a file exists in GCS."""
        try:
            blob = self.bucket.blob(name)
            return blob.exists()
        except Exception as e:
            logger.error(f"Failed to check if file exists {name}: {e}")
            return False

    def get_file_url(self, name: str, expire_seconds: int = 3600) -> str:
        """Generate a signed URL for GCS file."""
        try:
            if self.use_emulator:
                base_url = self.client_options.get('api_endpoint', 'http://localhost:9090')
                return f"{base_url}/storage/v1/b/{self.bucket_name}/o/{name.replace('/', '%2F')}?alt=media"
            else:
                blob = self.bucket.blob(name)
                return blob.generate_signed_url(expiration=expire_seconds)
                
        except Exception as e:
            logger.error(f"Failed to generate URL for file {name}: {e}")
            raise

    def list_files(self, prefix: str = "", delimiter: str = "/") -> Tuple[List[str], List[str]]:
        """List files and directories in GCS."""
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix, delimiter=delimiter)
            
            files = []
            dirs = []
            
            for blob in blobs:
                if blob.name != prefix:
                    files.append(blob.name[len(prefix):] if prefix else blob.name)
            
            dirs = [prefix[len(prefix):-1] for prefix in blobs.prefixes or []]
            
            return dirs, files
            
        except Exception as e:
            logger.error(f"Failed to list directory {prefix}: {e}")
            return [], []

    def get_file_size(self, name: str) -> int:
        """Get size of a file in GCS."""
        try:
            blob = self.bucket.blob(name)
            blob.reload()
            return blob.size or 0
        except Exception as e:
            logger.error(f"Failed to get size of file {name}: {e}")
            return 0

    def get_file_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a file in GCS."""
        try:
            blob = self.bucket.blob(name)
            blob.reload()
            return {
                'size': blob.size,
                'content_type': blob.content_type,
                'created_time': blob.time_created,
                'modified_time': blob.updated,
                'etag': blob.etag,
                'metadata': blob.metadata or {}
            }
        except Exception:
            return {}


class OrganizationScopedGCSStorage(GCSStorage, OrganizationScopedStorageMixin):
    """
    Organization-scoped GCS storage that enforces RBAC.
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

    def save_file(self, name: str, content, content_type: str = None, metadata: Dict[str, Any] = None) -> str:
        """Save file with organization scoping."""
        scoped_name = self.get_scoped_name(name)
        return super().save_file(scoped_name, content, content_type, metadata)

    def get_file(self, name: str):
        """Get file with organization scoping."""
        scoped_name = self.get_scoped_name(name)
        return super().get_file(scoped_name)

    def delete_file(self, name: str) -> bool:
        """Delete file with organization scoping."""
        scoped_name = self.get_scoped_name(name)
        return super().delete_file(scoped_name)

    def file_exists(self, name: str) -> bool:
        """Check file existence with organization scoping."""
        scoped_name = self.get_scoped_name(name)
        return super().file_exists(scoped_name)

    def get_file_size(self, name: str) -> int:
        """Get file size with organization scoping."""
        scoped_name = self.get_scoped_name(name)
        return super().get_file_size(scoped_name)

    def get_file_url(self, name: str, expire_seconds: int = 3600) -> str:
        """Get file URL with organization scoping."""
        scoped_name = self.get_scoped_name(name)
        return super().get_file_url(scoped_name, expire_seconds)

    def list_files(self, prefix: str = "", delimiter: str = "/") -> Tuple[List[str], List[str]]:
        """List files with organization scoping."""
        scoped_prefix = self.get_scoped_name(prefix) if prefix else self.get_organization_prefix(self.get_current_organization_id())
        return super().list_files(scoped_prefix, delimiter)

    def get_file_metadata(self, name: str) -> Dict[str, Any]:
        """Get file metadata with organization scoping."""
        scoped_name = self.get_scoped_name(name)
        return super().get_file_metadata(scoped_name)


# Register GCS backends with the factory
CloudStorageFactory.register_backend('gcs', GCSStorage)
CloudStorageFactory.register_backend('gcs_org', OrganizationScopedGCSStorage)


# Backward compatibility: keep the original class names
GCSStorage = GCSStorage
OrganizationScopedGCSStorage = OrganizationScopedGCSStorage