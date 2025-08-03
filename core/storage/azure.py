"""
Azure Blob Storage backend implementation using the abstract storage interface.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from django.conf import settings
from .base import BaseCloudStorage, OrganizationScopedStorageMixin, CloudStorageFactory

logger = logging.getLogger(__name__)


class AzureBlobStorage(BaseCloudStorage):
    """
    Azure Blob Storage implementation of the abstract storage interface.
    """

    def __init__(self, container_name=None, account_name=None, account_key=None, 
                 connection_string=None, sas_token=None, **kwargs):
        """
        Initialize Azure Blob storage backend.
        
        Args:
            container_name: Azure container name
            account_name: Azure storage account name
            account_key: Azure storage account key
            connection_string: Azure storage connection string
            sas_token: Azure SAS token
        """
        super().__init__(**kwargs)
        
        # Use provided values or try to get from settings, with sensible defaults
        self.container_name = container_name
        if self.container_name is None:
            try:
                from django.conf import settings
                self.container_name = getattr(settings, 'CLOUD_STORAGE_BUCKET_NAME', 'dev-app-assets')
            except:
                self.container_name = 'dev-app-assets'
        
        self.account_name = account_name
        if self.account_name is None:
            try:
                from django.conf import settings
                self.account_name = getattr(settings, 'AZURE_ACCOUNT_NAME', None)
            except:
                self.account_name = None
        
        self.account_key = account_key
        if self.account_key is None:
            try:
                from django.conf import settings
                self.account_key = getattr(settings, 'AZURE_ACCOUNT_KEY', None)
            except:
                self.account_key = None
        
        self.connection_string = connection_string
        if self.connection_string is None:
            try:
                from django.conf import settings
                self.connection_string = getattr(settings, 'AZURE_CONNECTION_STRING', None)
            except:
                self.connection_string = None
        
        self.sas_token = sas_token
        if self.sas_token is None:
            try:
                from django.conf import settings
                self.sas_token = getattr(settings, 'AZURE_SAS_TOKEN', None)
            except:
                self.sas_token = None
        
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Azure Blob client."""
        if self._client is None:
            try:
                from azure.storage.blob import BlobServiceClient
                
                if self.connection_string:
                    self._client = BlobServiceClient.from_connection_string(self.connection_string)
                elif self.account_name and self.account_key:
                    account_url = f"https://{self.account_name}.blob.core.windows.net"
                    self._client = BlobServiceClient(account_url=account_url, credential=self.account_key)
                elif self.account_name and self.sas_token:
                    account_url = f"https://{self.account_name}.blob.core.windows.net"
                    self._client = BlobServiceClient(account_url=account_url, credential=self.sas_token)
                else:
                    raise ValueError("Must provide either connection_string or account_name with account_key/sas_token")
                
                # Ensure container exists
                try:
                    self._client.create_container(self.container_name)
                except Exception:
                    pass  # Container may already exist
                    
            except ImportError:
                logger.error("azure-storage-blob is required but not installed")
                raise ImportError(
                    "azure-storage-blob is required for Azure Blob storage backend. "
                    "Install it with: pip install azure-storage-blob"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob client: {e}")
                raise

        return self._client

    def save_file(self, name: str, content, content_type: str = None, metadata: Dict[str, Any] = None) -> str:
        """Save a file to Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=name)
            
            kwargs = {}
            if content_type:
                kwargs['content_type'] = content_type
            elif hasattr(content, 'content_type'):
                kwargs['content_type'] = content.content_type
            
            if metadata:
                kwargs['metadata'] = {str(k): str(v) for k, v in metadata.items()}
            
            blob_client.upload_blob(content, overwrite=True, **kwargs)
            
            logger.info(f"Successfully saved file: {name}")
            return name
            
        except Exception as e:
            logger.error(f"Failed to save file {name}: {e}")
            raise

    def get_file(self, name: str):
        """Get a file from Azure Blob Storage."""
        try:
            from io import BytesIO
            
            blob_client = self.client.get_blob_client(container=self.container_name, blob=name)
            stream = BytesIO()
            blob_client.download_blob().readinto(stream)
            stream.seek(0)
            return stream
        except Exception as e:
            logger.error(f"Failed to open file {name}: {e}")
            raise

    def delete_file(self, name: str) -> bool:
        """Delete a file from Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=name)
            blob_client.delete_blob()
            logger.info(f"Successfully deleted file: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {name}: {e}")
            return False

    def file_exists(self, name: str) -> bool:
        """Check if a file exists in Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=name)
            return blob_client.exists()
        except Exception as e:
            logger.error(f"Failed to check if file exists {name}: {e}")
            return False

    def get_file_url(self, name: str, expire_seconds: int = 3600) -> str:
        """Generate a signed URL for Azure Blob file."""
        try:
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            from datetime import datetime, timedelta
            
            blob_client = self.client.get_blob_client(container=self.container_name, blob=name)
            
            if self.account_key:
                # Generate SAS token
                sas_token = generate_blob_sas(
                    account_name=self.account_name,
                    container_name=self.container_name,
                    blob_name=name,
                    account_key=self.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(seconds=expire_seconds)
                )
                return f"{blob_client.url}?{sas_token}"
            else:
                # Return direct URL (may not be accessible without proper permissions)
                return blob_client.url
                
        except Exception as e:
            logger.error(f"Failed to generate URL for file {name}: {e}")
            raise

    def list_files(self, prefix: str = "", delimiter: str = "/") -> Tuple[List[str], List[str]]:
        """List files and directories in Azure Blob Storage."""
        try:
            container_client = self.client.get_container_client(self.container_name)
            
            # Azure doesn't have hierarchical structure, so we simulate it
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            files = []
            dirs = set()
            
            for blob in blobs:
                relative_path = blob.name[len(prefix):] if prefix else blob.name
                
                if delimiter in relative_path:
                    # This is in a subdirectory
                    dir_name = relative_path.split(delimiter)[0]
                    dirs.add(dir_name)
                else:
                    # This is a direct file
                    if relative_path:  # Skip empty names
                        files.append(relative_path)
            
            return list(dirs), files
            
        except Exception as e:
            logger.error(f"Failed to list directory {prefix}: {e}")
            return [], []

    def get_file_size(self, name: str) -> int:
        """Get size of a file in Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=name)
            properties = blob_client.get_blob_properties()
            return properties.size or 0
        except Exception as e:
            logger.error(f"Failed to get size of file {name}: {e}")
            return 0

    def get_file_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a file in Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=name)
            properties = blob_client.get_blob_properties()
            return {
                'size': properties.size,
                'content_type': properties.content_settings.content_type,
                'created_time': properties.creation_time,
                'modified_time': properties.last_modified,
                'etag': properties.etag,
                'metadata': properties.metadata or {}
            }
        except Exception:
            return {}


class OrganizationScopedAzureBlobStorage(AzureBlobStorage, OrganizationScopedStorageMixin):
    """
    Organization-scoped Azure Blob storage that enforces RBAC.
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


# Register Azure backends with the factory
CloudStorageFactory.register_backend('azure', AzureBlobStorage)
CloudStorageFactory.register_backend('azure_org', OrganizationScopedAzureBlobStorage)