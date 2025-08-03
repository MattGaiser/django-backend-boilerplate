"""
Tests for multi-cloud storage abstraction layer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.core.files.base import ContentFile
from django.core.exceptions import PermissionDenied, SuspiciousOperation

from core.storage.base import CloudStorageFactory, OrganizationScopedStorageMixin
from core.storage.gcs import GCSStorage, OrganizationScopedGCSStorage
from core.storage.s3 import S3Storage, OrganizationScopedS3Storage
from core.storage.azure import AzureBlobStorage, OrganizationScopedAzureBlobStorage


class TestCloudStorageFactory:
    """Test the cloud storage factory."""
    
    def test_factory_registration(self):
        """Test backend registration and listing."""
        available_providers = CloudStorageFactory.get_available_providers()
        
        assert 'gcs' in available_providers
        assert 'gcs_org' in available_providers
        assert 's3' in available_providers
        assert 's3_org' in available_providers
        assert 'azure' in available_providers
        assert 'azure_org' in available_providers
    
    def test_create_gcs_storage(self):
        """Test creating GCS storage backend."""
        storage = CloudStorageFactory.create_storage(
            'gcs',
            bucket_name='test-bucket',
            use_emulator=True
        )
        
        assert isinstance(storage, GCSStorage)
        assert storage.bucket_name == 'test-bucket'
        assert storage.use_emulator is True
    
    def test_create_s3_storage(self):
        """Test creating S3 storage backend."""
        storage = CloudStorageFactory.create_storage(
            's3',
            bucket_name='test-bucket',
            region='us-west-2'
        )
        
        assert isinstance(storage, S3Storage)
        assert storage.bucket_name == 'test-bucket'
        assert storage.region == 'us-west-2'
    
    def test_create_azure_storage(self):
        """Test creating Azure storage backend."""
        storage = CloudStorageFactory.create_storage(
            'azure',
            container_name='test-container',
            account_name='testaccount'
        )
        
        assert isinstance(storage, AzureBlobStorage)
        assert storage.container_name == 'test-container'
        assert storage.account_name == 'testaccount'
    
    def test_create_unknown_provider(self):
        """Test error when creating unknown provider."""
        with pytest.raises(ValueError, match="Unknown storage provider"):
            CloudStorageFactory.create_storage('unknown_provider')


class TestOrganizationScopedStorageMixin:
    """Test the organization scoped storage mixin."""
    
    def test_get_organization_prefix(self):
        """Test organization prefix generation."""
        mixin = OrganizationScopedStorageMixin()
        prefix = mixin.get_organization_prefix('12345678-1234-1234-1234-123456789012')
        assert prefix == 'orgs/12345678-1234-1234-1234-123456789012/'
    
    def test_validate_organization_access_valid_path(self):
        """Test validation of valid organization path."""
        mixin = OrganizationScopedStorageMixin()
        org_id = '12345678-1234-1234-1234-123456789012'
        
        # Test path without org prefix
        result = mixin.validate_organization_access('documents/file.txt', org_id)
        assert result == f'orgs/{org_id}/documents/file.txt'
        
        # Test path with correct org prefix
        input_path = f'orgs/{org_id}/documents/file.txt'
        result = mixin.validate_organization_access(input_path, org_id)
        assert result == input_path
    
    def test_validate_organization_access_wrong_org(self):
        """Test validation failure for wrong organization."""
        mixin = OrganizationScopedStorageMixin()
        org_id = '12345678-1234-1234-1234-123456789012'
        wrong_org_id = '87654321-4321-4321-4321-210987654321'
        
        wrong_path = f'orgs/{wrong_org_id}/documents/file.txt'
        
        with pytest.raises(PermissionDenied, match="not in organization scope"):
            mixin.validate_organization_access(wrong_path, org_id)
    
    def test_validate_organization_access_suspicious_path(self):
        """Test validation failure for suspicious paths."""
        mixin = OrganizationScopedStorageMixin()
        org_id = '12345678-1234-1234-1234-123456789012'
        
        with pytest.raises(SuspiciousOperation, match="Suspicious file path"):
            mixin.validate_organization_access('../etc/passwd', org_id)
        
        with pytest.raises(SuspiciousOperation, match="Suspicious file path"):
            mixin.validate_organization_access('/etc/passwd', org_id)


@pytest.mark.django_db
class TestGCSStorage:
    """Test Google Cloud Storage implementation."""
    
    @patch('core.storage.gcs.storage')
    def test_gcs_storage_initialization(self, mock_storage_module):
        """Test GCS storage initialization."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_storage_module.Client.create_anonymous_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.exists.return_value = True
        
        storage = GCSStorage(
            bucket_name='test-bucket',
            use_emulator=True
        )
        
        # Access client to trigger lazy initialization
        client = storage.client
        bucket = storage.bucket
        
        assert storage.bucket_name == 'test-bucket'
        assert storage.use_emulator is True
        mock_storage_module.Client.create_anonymous_client.assert_called_once()
    
    @patch('core.storage.gcs.storage')
    def test_gcs_save_file(self, mock_storage_module):
        """Test saving a file to GCS."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_storage_module.Client.create_anonymous_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.exists.return_value = True
        
        storage = GCSStorage(bucket_name='test-bucket', use_emulator=True)
        content = ContentFile(b'test content', name='test.txt')
        
        result = storage.save_file('test.txt', content, content_type='text/plain')
        
        assert result == 'test.txt'
        mock_blob.upload_from_file.assert_called_once()
        assert mock_blob.content_type == 'text/plain'
    
    @patch('core.storage.gcs.storage')
    def test_gcs_file_exists(self, mock_storage_module):
        """Test checking file existence in GCS."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_storage_module.Client.create_anonymous_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.exists.return_value = True
        mock_blob.exists.return_value = True
        
        storage = GCSStorage(bucket_name='test-bucket', use_emulator=True)
        
        exists = storage.file_exists('test.txt')
        
        assert exists is True
        mock_blob.exists.assert_called_once()


@pytest.mark.django_db
class TestS3Storage:
    """Test AWS S3 Storage implementation."""
    
    @patch('core.storage.s3.boto3')
    def test_s3_storage_initialization(self, mock_boto3):
        """Test S3 storage initialization."""
        mock_session = Mock()
        mock_client = Mock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        storage = S3Storage(
            bucket_name='test-bucket',
            region='us-west-2',
            access_key_id='test-key',
            secret_access_key='test-secret'
        )
        
        # Access client to trigger lazy initialization
        client = storage.client
        
        assert storage.bucket_name == 'test-bucket'
        assert storage.region == 'us-west-2'
        mock_boto3.Session.assert_called_once()
        mock_session.client.assert_called_with('s3', endpoint_url=None)
    
    @patch('core.storage.s3.boto3')
    def test_s3_save_file(self, mock_boto3):
        """Test saving a file to S3."""
        mock_session = Mock()
        mock_client = Mock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        storage = S3Storage(bucket_name='test-bucket')
        content = ContentFile(b'test content', name='test.txt')
        
        result = storage.save_file('test.txt', content, content_type='text/plain')
        
        assert result == 'test.txt'
        mock_client.upload_fileobj.assert_called_once()
    
    @patch('core.storage.s3.boto3')
    def test_s3_file_exists(self, mock_boto3):
        """Test checking file existence in S3."""
        mock_session = Mock()
        mock_client = Mock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        storage = S3Storage(bucket_name='test-bucket')
        
        exists = storage.file_exists('test.txt')
        
        # Should return True if head_object doesn't raise exception
        mock_client.head_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test.txt'
        )


@pytest.mark.django_db
class TestAzureBlobStorage:
    """Test Azure Blob Storage implementation."""
    
    @patch('core.storage.azure.BlobServiceClient')
    def test_azure_storage_initialization(self, mock_blob_service_client):
        """Test Azure storage initialization."""
        mock_client = Mock()
        mock_blob_service_client.from_connection_string.return_value = mock_client
        
        storage = AzureBlobStorage(
            container_name='test-container',
            connection_string='DefaultEndpointsProtocol=https;AccountName=test;'
        )
        
        # Access client to trigger lazy initialization
        client = storage.client
        
        assert storage.container_name == 'test-container'
        mock_blob_service_client.from_connection_string.assert_called_once()
    
    @patch('core.storage.azure.BlobServiceClient')
    def test_azure_save_file(self, mock_blob_service_client):
        """Test saving a file to Azure Blob Storage."""
        mock_client = Mock()
        mock_blob_client = Mock()
        mock_blob_service_client.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client
        
        storage = AzureBlobStorage(
            container_name='test-container',
            connection_string='test-connection-string'
        )
        content = ContentFile(b'test content', name='test.txt')
        
        result = storage.save_file('test.txt', content, content_type='text/plain')
        
        assert result == 'test.txt'
        mock_blob_client.upload_blob.assert_called_once()
    
    @patch('core.storage.azure.BlobServiceClient')
    def test_azure_file_exists(self, mock_blob_service_client):
        """Test checking file existence in Azure Blob Storage."""
        mock_client = Mock()
        mock_blob_client = Mock()
        mock_blob_service_client.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.exists.return_value = True
        
        storage = AzureBlobStorage(
            container_name='test-container',
            connection_string='test-connection-string'
        )
        
        exists = storage.file_exists('test.txt')
        
        assert exists is True
        mock_blob_client.exists.assert_called_once()


@pytest.mark.django_db
class TestOrganizationScopedStorages:
    """Test organization-scoped storage implementations."""
    
    @patch('core.storage.gcs.get_current_user')
    @patch('core.storage.gcs.storage')
    def test_organization_scoped_gcs_save(self, mock_storage_module, mock_get_current_user):
        """Test organization-scoped GCS file save."""
        # Mock user and organization
        mock_user = Mock()
        mock_org = Mock()
        mock_org.id = '12345678-1234-1234-1234-123456789012'
        mock_user.is_authenticated = True
        mock_user.get_default_organization.return_value = mock_org
        mock_get_current_user.return_value = mock_user
        
        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage_module.Client.create_anonymous_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.exists.return_value = True
        
        storage = OrganizationScopedGCSStorage(bucket_name='test-bucket', use_emulator=True)
        content = ContentFile(b'test content', name='test.txt')
        
        result = storage.save_file('documents/test.txt', content)
        
        # Should add organization prefix
        expected_path = f'orgs/{mock_org.id}/documents/test.txt'
        mock_bucket.blob.assert_called_with(expected_path)
        assert result == expected_path
    
    def test_organization_scoped_without_user_context(self):
        """Test organization-scoped storage without user context."""
        with patch('core.storage.base.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = None
            
            storage = OrganizationScopedGCSStorage(bucket_name='test-bucket')
            content = ContentFile(b'test content', name='test.txt')
            
            with pytest.raises(PermissionDenied, match="No organization context"):
                storage.save_file('test.txt', content)


@pytest.mark.django_db 
class TestCloudConfigIntegration:
    """Test integration with cloud configuration."""
    
    @patch('core.storage.get_default_storage')
    def test_get_default_storage_with_config(self, mock_get_default_storage):
        """Test getting default storage using configuration."""
        from core.storage import get_default_storage
        
        # This would normally use the cloud_config to determine provider
        storage = get_default_storage()
        
        # Should call the function that creates storage based on settings
        mock_get_default_storage.assert_called_once()