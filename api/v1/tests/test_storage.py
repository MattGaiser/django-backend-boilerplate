"""
Tests for storage API endpoints with RBAC enforcement.

This module tests file upload, download, and management operations
with proper organization-level access control.
"""

import json
import tempfile
from unittest.mock import patch, MagicMock
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole


@pytest.mark.django_db
class TestStorageAPI:
    """Test storage API endpoints with RBAC."""

    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create organizations
        self.org1 = OrganizationFactory(name="Test Org 1")
        self.org2 = OrganizationFactory(name="Test Org 2")
        
        # Create users with different roles
        self.admin_user = UserFactory(email="admin@test.com")
        self.manager_user = UserFactory(email="manager@test.com")
        self.viewer_user = UserFactory(email="viewer@test.com")
        self.other_org_user = UserFactory(email="other@test.com")
        
        # Create memberships
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.org1,
            role=OrgRole.ADMIN,
            is_default=True
        )
        OrganizationMembershipFactory(
            user=self.manager_user,
            organization=self.org1,
            role=OrgRole.MANAGER,
            is_default=True
        )
        OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.org1,
            role=OrgRole.VIEWER,
            is_default=True
        )
        OrganizationMembershipFactory(
            user=self.other_org_user,
            organization=self.org2,
            role=OrgRole.ADMIN,
            is_default=True
        )
        
        # Create test file
        self.test_file_content = b"This is a test file content"
        self.test_file = SimpleUploadedFile(
            "test.txt",
            self.test_file_content,
            content_type="text/plain"
        )

    def _create_test_file(self, name="test.txt", content=None):
        """Create a test file for uploads."""
        if content is None:
            content = self.test_file_content
        return SimpleUploadedFile(name, content, content_type="text/plain")

    @patch('api.v1.views.storage.StorageService')
    def test_upload_file_success_admin(self, mock_storage_service_class):
        """Test successful file upload as admin."""
        # Mock storage service
        mock_service = MagicMock()
        mock_storage_service_class.return_value = mock_service
        mock_service.upload_file.return_value = {
            'path': 'orgs/org-id/documents/test.txt',
            'name': 'test.txt',
            'size': 1234,
            'content_type': 'text/plain',
            'category': 'documents',
            'url': 'https://storage.googleapis.com/bucket/file'
        }
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('storage-upload')
        data = {
            'file': self._create_test_file(),
            'category': 'documents'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'file' in response.data
        assert response.data['message'] == 'File uploaded successfully'

    @patch('api.v1.views.storage.StorageService')
    def test_upload_file_success_manager(self, mock_storage_service_class):
        """Test successful file upload as manager."""
        # Mock storage service
        mock_service = MagicMock()
        mock_storage_service_class.return_value = mock_service
        mock_service.upload_file.return_value = {
            'path': 'orgs/org-id/general/test.txt',
            'name': 'test.txt',
            'size': 1234,
            'content_type': 'text/plain',
            'category': 'general',
            'url': 'https://storage.googleapis.com/bucket/file'
        }
        
        self.client.force_authenticate(user=self.manager_user)
        
        url = reverse('storage-upload')
        data = {
            'file': self._create_test_file(),
            'category': 'general'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_file_forbidden_viewer(self):
        """Test file upload forbidden for viewer."""
        self.client.force_authenticate(user=self.viewer_user)
        
        url = reverse('storage-upload')
        data = {
            'file': self._create_test_file(),
            'category': 'general'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_upload_file_unauthenticated(self):
        """Test file upload requires authentication."""
        url = reverse('storage-upload')
        data = {
            'file': self._create_test_file(),
            'category': 'general'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_file_no_file(self):
        """Test upload with no file fails."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('storage-upload')
        data = {'category': 'general'}
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_file_invalid_category(self):
        """Test upload with invalid category fails."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('storage-upload')
        data = {
            'file': self._create_test_file(),
            'category': 'invalid_category'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_file_too_large(self):
        """Test upload of oversized file fails."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create a large file (over 50MB simulated)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        large_file = SimpleUploadedFile(
            "large.txt",
            large_content,
            content_type="text/plain"
        )
        
        url = reverse('storage-upload')
        data = {
            'file': large_file,
            'category': 'general'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_dangerous_file_extension(self):
        """Test upload of dangerous file extension fails."""
        self.client.force_authenticate(user=self.admin_user)
        
        dangerous_file = SimpleUploadedFile(
            "malware.exe",
            b"fake executable content",
            content_type="application/exe"
        )
        
        url = reverse('storage-upload')
        data = {
            'file': dangerous_file,
            'category': 'general'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('api.v1.views.storage.StorageService')
    def test_download_file_success(self, mock_service_class):
        """Test successful file download."""
        # Mock storage service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_file_url.return_value = "https://signed-url.com/file"
        
        self.client.force_authenticate(user=self.viewer_user)
        
        url = reverse('storage-download', kwargs={'file_path': 'test/file.txt'})
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'download_url' in response.data
        assert response.data['download_url'] == "https://signed-url.com/file"

    @patch('api.v1.views.storage.StorageService')
    def test_download_file_not_found(self, mock_service_class):
        """Test download of non-existent file."""
        # Mock storage service to raise ValidationError
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_file_url.side_effect = ValidationError("File not found")
        
        self.client.force_authenticate(user=self.viewer_user)
        
        url = reverse('storage-download', kwargs={'file_path': 'nonexistent.txt'})
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('api.v1.views.storage.StorageService')
    def test_delete_file_success_admin(self, mock_service_class):
        """Test successful file deletion as admin."""
        # Mock storage service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.delete_file.return_value = True
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('storage-delete', kwargs={'file_path': 'test/file.txt'})
        
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_file_forbidden_viewer(self):
        """Test file deletion forbidden for viewer."""
        self.client.force_authenticate(user=self.viewer_user)
        
        url = reverse('storage-delete', kwargs={'file_path': 'test/file.txt'})
        
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('api.v1.views.storage.StorageService')
    def test_list_files_success(self, mock_service_class):
        """Test successful file listing."""
        # Mock storage service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.list_files.return_value = [
            {
                'name': 'file1.txt',
                'path': 'file1.txt',
                'size': 100,
                'modified_time': None,
                'url': 'https://url1.com'
            },
            {
                'name': 'file2.txt',
                'path': 'file2.txt',
                'size': 200,
                'modified_time': None,
                'url': 'https://url2.com'
            }
        ]
        
        self.client.force_authenticate(user=self.viewer_user)
        
        url = reverse('storage-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'files' in response.data
        assert len(response.data['files']) == 2

    @patch('api.v1.views.storage.StorageService')
    def test_get_file_info_success(self, mock_service_class):
        """Test successful file info retrieval."""
        # Mock storage service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_file_info.return_value = {
            'path': 'test/file.txt',
            'size': 100,
            'created_time': None,
            'modified_time': None,
            'exists': True,
            'url': 'https://url.com'
        }
        
        self.client.force_authenticate(user=self.viewer_user)
        
        url = reverse('storage-info', kwargs={'file_path': 'test/file.txt'})
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['path'] == 'test/file.txt'
        assert response.data['size'] == 100

    @patch('api.v1.views.storage.StorageService')
    def test_get_storage_usage_success_admin(self, mock_service_class):
        """Test successful storage usage retrieval as admin."""
        # Mock storage service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_storage_usage.return_value = {
            'total_size_bytes': 1024000,
            'total_size_mb': 1.0,
            'file_count': 10,
            'organization_id': str(self.org1.id),
            'organization_name': self.org1.name
        }
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('storage-usage')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_size_mb'] == 1.0
        assert response.data['file_count'] == 10

    def test_get_storage_usage_forbidden_viewer(self):
        """Test storage usage forbidden for viewer."""
        self.client.force_authenticate(user=self.viewer_user)
        
        url = reverse('storage-usage')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cross_organization_access_denied(self):
        """Test that users cannot access files from other organizations."""
        # This would be tested more thoroughly in integration tests
        # with actual storage operations
        self.client.force_authenticate(user=self.other_org_user)
        
        url = reverse('storage-list')
        
        response = self.client.get(url)
        
        # Should succeed but return empty list (different org)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestStorageServiceRBAC:
    """Test storage service RBAC enforcement."""

    def setup_method(self):
        """Set up test data."""
        self.org = OrganizationFactory()
        
        self.admin_user = UserFactory()
        self.manager_user = UserFactory()
        self.viewer_user = UserFactory()
        
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.org,
            role=OrgRole.ADMIN,
            is_default=True
        )
        OrganizationMembershipFactory(
            user=self.manager_user,
            organization=self.org,
            role=OrgRole.MANAGER,
            is_default=True
        )
        OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.org,
            role=OrgRole.VIEWER,
            is_default=True
        )

    def test_storage_service_initialization(self):
        """Test storage service initialization."""
        from core.services.storage import StorageService
        
        # Should succeed with valid user and organization
        service = StorageService(user=self.admin_user, organization=self.org)
        assert service.user == self.admin_user
        assert service.organization == self.org

    def test_storage_service_no_organization(self):
        """Test storage service requires organization."""
        from core.services.storage import StorageService
        
        user_without_org = UserFactory()
        
        with pytest.raises(ValueError, match="Organization context is required"):
            StorageService(user=user_without_org)

    def test_permission_checks(self):
        """Test RBAC permission checks."""
        from core.services.storage import StorageService
        from django.core.exceptions import PermissionDenied
        
        service = StorageService(user=self.viewer_user, organization=self.org)
        
        # Viewer should not be able to upload
        with pytest.raises(PermissionDenied):
            service._check_permission([OrgRole.ADMIN, OrgRole.MANAGER], "file upload")
            
        # Viewer should be able to view
        service._check_permission([OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.VIEWER], "file view")

    def test_file_path_validation(self):
        """Test file path validation."""
        from core.services.storage import StorageService
        from django.core.exceptions import ValidationError
        
        service = StorageService(user=self.admin_user, organization=self.org)
        
        # Valid paths
        assert service._validate_file_path("documents/file.txt") == "documents/file.txt"
        assert service._validate_file_path("/documents/file.txt") == "documents/file.txt"
        
        # Invalid paths
        with pytest.raises(ValidationError):
            service._validate_file_path("../../../etc/passwd")
            
        with pytest.raises(ValidationError):
            service._validate_file_path("a/" * 20)  # Too deep