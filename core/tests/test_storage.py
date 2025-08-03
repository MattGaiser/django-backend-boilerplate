"""
Tests for GCS storage backend with RBAC enforcement.

This module tests the Google Cloud Storage integration with
organization-scoped access control.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.conf import settings

from core.storage import GCSStorage, OrganizationScopedGCSStorage
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole


@pytest.mark.django_db
class TestGCSStorage:
    """Test base GCS storage functionality."""

    def setup_method(self):
        """Set up test data."""
        self.bucket_name = "test-bucket"
        self.storage = GCSStorage(bucket_name=self.bucket_name)

    @patch('core.storage.storage')
    def test_client_initialization_production(self, mock_storage_module):
        """Test GCS client initialization for production."""
        mock_client = MagicMock()
        mock_storage_module.Client.return_value = mock_client
        
        with patch('google.cloud.storage'):
            storage = GCSStorage(bucket_name="test", client_options={})
            
            # Access client property to trigger initialization
            client = storage.client
            
            assert client == mock_client

    @patch('google.cloud.storage')
    def test_client_initialization_emulator(self, mock_storage_module):
        """Test GCS client initialization for emulator."""
        mock_client = MagicMock()
        mock_storage_module.Client.create_anonymous_client.return_value = mock_client
        
        storage = GCSStorage(
            bucket_name="test",
            client_options={'api_endpoint': 'http://localhost:9090'}
        )
        storage.use_emulator = True
        
        # Access client property to trigger initialization
        client = storage.client
        
        assert client == mock_client
        mock_storage_module.Client.create_anonymous_client.assert_called_once()

    @patch('google.cloud.storage')
    def test_bucket_initialization(self, mock_storage_module):
        """Test GCS bucket initialization."""
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_storage_module.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        
        storage = GCSStorage(bucket_name="test-bucket")
        
        # Access bucket property to trigger initialization
        bucket = storage.bucket
        
        assert bucket == mock_bucket
        mock_client.bucket.assert_called_once_with("test-bucket")

    def test_organization_prefix_generation(self):
        """Test organization prefix generation."""
        org_id = "12345678-1234-1234-1234-123456789012"
        expected_prefix = f"orgs/{org_id}/"
        
        result = self.storage._get_organization_prefix(org_id)
        
        assert result == expected_prefix

    def test_validate_organization_access_valid_path(self):
        """Test organization access validation with valid path."""
        org_id = "12345678-1234-1234-1234-123456789012"
        file_path = "documents/file.txt"
        
        result = self.storage._validate_organization_access(file_path, org_id)
        
        assert result == f"orgs/{org_id}/documents/file.txt"

    def test_validate_organization_access_already_prefixed(self):
        """Test organization access validation with already prefixed path."""
        org_id = "12345678-1234-1234-1234-123456789012"
        file_path = f"orgs/{org_id}/documents/file.txt"
        
        result = self.storage._validate_organization_access(file_path, org_id)
        
        assert result == file_path

    def test_validate_organization_access_suspicious_path(self):
        """Test organization access validation rejects suspicious paths."""
        org_id = "12345678-1234-1234-1234-123456789012"
        
        with pytest.raises(SuspiciousOperation):
            self.storage._validate_organization_access("../../../etc/passwd", org_id)
            
        with pytest.raises(SuspiciousOperation):
            self.storage._validate_organization_access("/etc/passwd", org_id)

    def test_validate_organization_access_wrong_org(self):
        """Test organization access validation rejects wrong organization."""
        org_id = "12345678-1234-1234-1234-123456789012"
        other_org_id = "87654321-4321-4321-4321-210987654321"
        file_path = f"orgs/{other_org_id}/documents/file.txt"
        
        with pytest.raises(PermissionDenied):
            self.storage._validate_organization_access(file_path, org_id)

    @patch.object(GCSStorage, 'bucket', new_callable=PropertyMock)
    def test_save_file(self, mock_bucket_prop):
        """Test saving a file to GCS."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket_prop.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        content = SimpleUploadedFile("test.txt", b"test content", content_type="text/plain")
        file_path = "test/file.txt"
        
        result = self.storage._save(file_path, content)
        
        assert result == file_path
        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.upload_from_file.assert_called_once_with(content, rewind=True)

    @patch.object(GCSStorage, 'bucket', new_callable=PropertyMock)
    def test_open_file(self, mock_bucket_prop):
        """Test opening a file from GCS."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_file = MagicMock()
        mock_bucket_prop.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.open.return_value = mock_file
        
        file_path = "test/file.txt"
        
        result = self.storage._open(file_path)
        
        assert result == mock_file
        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.open.assert_called_once_with('rb')

    @patch.object(GCSStorage, 'bucket', new_callable=PropertyMock)
    def test_delete_file(self, mock_bucket_prop):
        """Test deleting a file from GCS."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket_prop.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        file_path = "test/file.txt"
        
        self.storage.delete(file_path)
        
        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.delete.assert_called_once()

    @patch.object(GCSStorage, 'bucket', new_callable=PropertyMock)
    def test_exists_file(self, mock_bucket_prop):
        """Test checking if a file exists in GCS."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket_prop.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        
        file_path = "test/file.txt"
        
        result = self.storage.exists(file_path)
        
        assert result is True
        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.exists.assert_called_once()

    @patch.object(GCSStorage, 'bucket', new_callable=PropertyMock)
    def test_size_file(self, mock_bucket_prop):
        """Test getting file size from GCS."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket_prop.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.size = 1024
        
        file_path = "test/file.txt"
        
        result = self.storage.size(file_path)
        
        assert result == 1024
        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.reload.assert_called_once()

    @patch.object(GCSStorage, 'bucket', new_callable=PropertyMock)
    def test_url_production(self, mock_bucket_prop):
        """Test generating signed URL in production."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket_prop.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.generate_signed_url.return_value = "https://signed-url.com"
        
        self.storage.use_emulator = False
        file_path = "test/file.txt"
        
        result = self.storage.url(file_path)
        
        assert result == "https://signed-url.com"
        mock_blob.generate_signed_url.assert_called_once_with(expiration=3600)

    @patch.object(GCSStorage, 'bucket', new_callable=PropertyMock)
    def test_url_emulator(self, mock_bucket_prop):
        """Test generating URL for emulator."""
        mock_bucket = MagicMock()
        mock_bucket_prop.return_value = mock_bucket
        
        self.storage.use_emulator = True
        self.storage.client_options = {'api_endpoint': 'http://localhost:9090'}
        file_path = "test/file.txt"
        
        result = self.storage.url(file_path)
        
        expected_url = f"http://localhost:9090/storage/v1/b/{self.bucket_name}/o/test%2Ffile.txt?alt=media"
        assert result == expected_url


@pytest.mark.django_db
class TestOrganizationScopedGCSStorage:
    """Test organization-scoped GCS storage."""

    def setup_method(self):
        """Set up test data."""
        self.org = OrganizationFactory()
        self.user = UserFactory()
        OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN,
            is_default=True
        )
        
        self.storage = OrganizationScopedGCSStorage(
            organization_id=str(self.org.id),
            bucket_name="test-bucket"
        )

    def test_initialization_with_org_id(self):
        """Test initialization with organization ID."""
        org_id = str(self.org.id)
        storage = OrganizationScopedGCSStorage(organization_id=org_id)
        
        assert storage.organization_id == org_id

    @patch('core.signals.get_current_user')
    def test_get_current_organization_id_from_user(self, mock_get_user):
        """Test getting organization ID from current user."""
        mock_get_user.return_value = self.user
        
        storage = OrganizationScopedGCSStorage()
        org_id = storage._get_current_organization_id()
        
        assert org_id == str(self.org.id)

    @patch('core.signals.get_current_user')
    def test_get_current_organization_id_no_user(self, mock_get_user):
        """Test getting organization ID with no current user."""
        mock_get_user.return_value = None
        
        storage = OrganizationScopedGCSStorage()
        org_id = storage._get_current_organization_id()
        
        assert org_id is None

    def test_get_scoped_name_with_org_id(self):
        """Test getting scoped name with organization ID."""
        file_name = "documents/file.txt"
        
        result = self.storage._get_scoped_name(file_name)
        
        expected = f"orgs/{self.org.id}/documents/file.txt"
        assert result == expected

    def test_get_scoped_name_no_org_context(self):
        """Test getting scoped name without organization context."""
        storage = OrganizationScopedGCSStorage()
        file_name = "documents/file.txt"
        
        with pytest.raises(PermissionDenied, match="No organization context"):
            storage._get_scoped_name(file_name)

    @patch.object(OrganizationScopedGCSStorage, '_save')
    def test_save_with_scoping(self, mock_save):
        """Test save operation with organization scoping."""
        mock_save.return_value = f"orgs/{self.org.id}/test.txt"
        
        content = SimpleUploadedFile("test.txt", b"content")
        
        result = self.storage._save("test.txt", content)
        
        expected_path = f"orgs/{self.org.id}/test.txt"
        mock_save.assert_called_once_with(expected_path, content)
        assert result == expected_path

    @patch.object(OrganizationScopedGCSStorage, '_open')
    def test_open_with_scoping(self, mock_open):
        """Test open operation with organization scoping."""
        mock_file = MagicMock()
        mock_open.return_value = mock_file
        
        result = self.storage._open("test.txt")
        
        expected_path = f"orgs/{self.org.id}/test.txt"
        mock_open.assert_called_once_with(expected_path, 'rb')
        assert result == mock_file

    @patch.object(OrganizationScopedGCSStorage, 'delete')
    def test_delete_with_scoping(self, mock_delete):
        """Test delete operation with organization scoping."""
        self.storage.delete("test.txt")
        
        expected_path = f"orgs/{self.org.id}/test.txt"
        mock_delete.assert_called_once_with(expected_path)

    @patch.object(OrganizationScopedGCSStorage, 'exists')
    def test_exists_with_scoping(self, mock_exists):
        """Test exists operation with organization scoping."""
        mock_exists.return_value = True
        
        result = self.storage.exists("test.txt")
        
        expected_path = f"orgs/{self.org.id}/test.txt"
        mock_exists.assert_called_once_with(expected_path)
        assert result is True

    @patch.object(OrganizationScopedGCSStorage, 'url')
    def test_url_with_scoping(self, mock_url):
        """Test URL generation with organization scoping."""
        mock_url.return_value = "https://signed-url.com"
        
        result = self.storage.url("test.txt")
        
        expected_path = f"orgs/{self.org.id}/test.txt"
        mock_url.assert_called_once_with(expected_path, 3600)
        assert result == "https://signed-url.com"

    @patch.object(OrganizationScopedGCSStorage, 'size')
    def test_size_with_scoping(self, mock_size):
        """Test size operation with organization scoping."""
        mock_size.return_value = 1024
        
        result = self.storage.size("test.txt")
        
        expected_path = f"orgs/{self.org.id}/test.txt"
        mock_size.assert_called_once_with(expected_path)
        assert result == 1024

    @patch.object(OrganizationScopedGCSStorage, 'listdir')
    def test_listdir_with_scoping(self, mock_listdir):
        """Test listdir operation with organization scoping."""
        mock_listdir.return_value = ([], ["file1.txt", "file2.txt"])
        
        result = self.storage.listdir("documents")
        
        expected_path = f"orgs/{self.org.id}/documents"
        mock_listdir.assert_called_once_with(expected_path)
        assert result == ([], ["file1.txt", "file2.txt"])


@pytest.mark.django_db 
class TestStorageIntegration:
    """Integration tests for storage with Django settings."""

    def test_storage_settings_production(self):
        """Test storage configuration for production."""
        with patch.object(settings, 'USE_GCS_EMULATOR', False):
            with patch.object(settings, 'GCS_CLIENT_OPTIONS', {}):
                storage = GCSStorage()
                
                assert not storage.use_emulator
                assert storage.client_options == {}

    def test_storage_settings_emulator(self):
        """Test storage configuration for emulator."""
        with patch.object(settings, 'USE_GCS_EMULATOR', True):
            with patch.object(settings, 'GCS_EMULATOR_HOST', 'http://localhost:9090'):
                with patch.object(settings, 'GCS_CLIENT_OPTIONS', {'api_endpoint': 'http://localhost:9090'}):
                    storage = GCSStorage()
                    
                    assert storage.use_emulator
                    assert storage.client_options['api_endpoint'] == 'http://localhost:9090'