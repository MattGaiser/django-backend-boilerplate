"""
AWS S3 storage backend implementation using the abstract storage interface.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from django.conf import settings
from .base import BaseCloudStorage, OrganizationScopedStorageMixin, CloudStorageFactory

logger = logging.getLogger(__name__)


class S3Storage(BaseCloudStorage):
    """
    AWS S3 implementation of the abstract storage interface.
    """

    def __init__(self, bucket_name=None, region=None, access_key_id=None, 
                 secret_access_key=None, endpoint_url=None, **kwargs):
        """
        Initialize S3 storage backend.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            endpoint_url: Custom S3 endpoint (for S3-compatible services)
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
        
        self.region = region
        if self.region is None:
            try:
                from django.conf import settings
                self.region = getattr(settings, 'AWS_S3_REGION', 'us-east-1')
            except:
                self.region = 'us-east-1'
        
        self.access_key_id = access_key_id
        if self.access_key_id is None:
            try:
                from django.conf import settings
                self.access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            except:
                self.access_key_id = None
        
        self.secret_access_key = secret_access_key
        if self.secret_access_key is None:
            try:
                from django.conf import settings
                self.secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            except:
                self.secret_access_key = None
        
        self.endpoint_url = endpoint_url
        if self.endpoint_url is None:
            try:
                from django.conf import settings
                self.endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
            except:
                self.endpoint_url = None
        
        self._client = None
        self._resource = None

    @property
    def client(self):
        """Lazy initialization of S3 client."""
        if self._client is None:
            try:
                import boto3
                
                session = boto3.Session(
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name=self.region
                )
                
                self._client = session.client(
                    's3',
                    endpoint_url=self.endpoint_url
                )
                
            except ImportError:
                logger.error("boto3 is required but not installed")
                raise ImportError(
                    "boto3 is required for S3 storage backend. "
                    "Install it with: pip install boto3"
                )
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                raise

        return self._client

    @property
    def resource(self):
        """Lazy initialization of S3 resource."""
        if self._resource is None:
            try:
                import boto3
                
                session = boto3.Session(
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name=self.region
                )
                
                self._resource = session.resource(
                    's3',
                    endpoint_url=self.endpoint_url
                )
                
            except Exception as e:
                logger.error(f"Failed to initialize S3 resource: {e}")
                raise

        return self._resource

    def save_file(self, name: str, content, content_type: str = None, metadata: Dict[str, Any] = None) -> str:
        """Save a file to S3."""
        try:
            extra_args = {}
            
            if content_type:
                extra_args['ContentType'] = content_type
            elif hasattr(content, 'content_type'):
                extra_args['ContentType'] = content.content_type
            
            if metadata:
                extra_args['Metadata'] = {str(k): str(v) for k, v in metadata.items()}
            
            self.client.upload_fileobj(content, self.bucket_name, name, ExtraArgs=extra_args)
            
            logger.info(f"Successfully saved file: {name}")
            return name
            
        except Exception as e:
            logger.error(f"Failed to save file {name}: {e}")
            raise

    def get_file(self, name: str):
        """Get a file from S3."""
        try:
            from io import BytesIO
            
            obj = BytesIO()
            self.client.download_fileobj(self.bucket_name, name, obj)
            obj.seek(0)
            return obj
        except Exception as e:
            logger.error(f"Failed to open file {name}: {e}")
            raise

    def delete_file(self, name: str) -> bool:
        """Delete a file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=name)
            logger.info(f"Successfully deleted file: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {name}: {e}")
            return False

    def file_exists(self, name: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except self.client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Failed to check if file exists {name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to check if file exists {name}: {e}")
            return False

    def get_file_url(self, name: str, expire_seconds: int = 3600) -> str:
        """Generate a signed URL for S3 file."""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': name},
                ExpiresIn=expire_seconds
            )
            return url
                
        except Exception as e:
            logger.error(f"Failed to generate URL for file {name}: {e}")
            raise

    def list_files(self, prefix: str = "", delimiter: str = "/") -> Tuple[List[str], List[str]]:
        """List files and directories in S3."""
        try:
            kwargs = {
                'Bucket': self.bucket_name,
                'Prefix': prefix,
                'Delimiter': delimiter
            }
            
            response = self.client.list_objects_v2(**kwargs)
            
            files = []
            dirs = []
            
            # Get files
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'] != prefix:
                        files.append(obj['Key'][len(prefix):] if prefix else obj['Key'])
            
            # Get directories (common prefixes)
            if 'CommonPrefixes' in response:
                for prefix_info in response['CommonPrefixes']:
                    prefix_name = prefix_info['Prefix']
                    dirs.append(prefix_name[len(prefix):-1] if prefix else prefix_name[:-1])
            
            return dirs, files
            
        except Exception as e:
            logger.error(f"Failed to list directory {prefix}: {e}")
            return [], []

    def get_file_size(self, name: str) -> int:
        """Get size of a file in S3."""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=name)
            return response.get('ContentLength', 0)
        except Exception as e:
            logger.error(f"Failed to get size of file {name}: {e}")
            return 0

    def get_file_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a file in S3."""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=name)
            return {
                'size': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', ''),
                'created_time': response.get('LastModified'),
                'modified_time': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
        except Exception:
            return {}


class OrganizationScopedS3Storage(S3Storage, OrganizationScopedStorageMixin):
    """
    Organization-scoped S3 storage that enforces RBAC.
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


# Register S3 backends with the factory
CloudStorageFactory.register_backend('s3', S3Storage)
CloudStorageFactory.register_backend('s3_org', OrganizationScopedS3Storage)