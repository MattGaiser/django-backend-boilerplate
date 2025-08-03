"""
Storage service layer for handling file operations with RBAC enforcement.

This module provides high-level file storage operations that automatically
enforce organization-level access control and provide convenient methods
for common file operations.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import PermissionDenied, ValidationError
from django.conf import settings

from core.models import User, Organization
from core.storage import OrganizationScopedGCSStorage
from constants.roles import OrgRole

logger = logging.getLogger(__name__)


class StorageService:
    """
    High-level storage service with RBAC enforcement.
    
    This service provides organization-scoped file operations with proper
    access control based on user roles and organization membership.
    """

    def __init__(self, user: User, organization: Organization = None):
        """
        Initialize storage service for a specific user and organization.
        
        Args:
            user: User performing the operations
            organization: Organization context (defaults to user's default org)
        """
        self.user = user
        self.organization = organization or user.get_default_organization()
        
        if not self.organization:
            raise ValueError("Organization context is required for storage operations")
            
        # Verify user has access to the organization
        if not user.get_role(self.organization):
            raise PermissionDenied(f"User does not have access to organization {self.organization.name}")
            
        self.storage = OrganizationScopedGCSStorage(organization_id=str(self.organization.id))

    def _check_permission(self, required_roles: List[OrgRole], operation: str = "operation"):
        """
        Check if user has required permissions for the operation.
        
        Args:
            required_roles: List of roles that can perform the operation
            operation: Description of the operation for error messages
            
        Raises:
            PermissionDenied: If user doesn't have required permissions
        """
        user_role = self.user.get_role(self.organization)
        if user_role not in [role.value for role in required_roles]:
            raise PermissionDenied(
                f"User role '{user_role}' insufficient for {operation}. "
                f"Required roles: {[role.value for role in required_roles]}"
            )

    def _validate_file_path(self, file_path: str) -> str:
        """
        Validate and normalize file path.
        
        Args:
            file_path: File path to validate
            
        Returns:
            Normalized file path
            
        Raises:
            ValidationError: If path is invalid
        """
        # Remove leading slashes and normalize path
        file_path = file_path.lstrip('/')
        path = Path(file_path)
        
        # Check for suspicious path components
        if any(part in ['..', '.', ''] for part in path.parts):
            raise ValidationError(f"Invalid file path: {file_path}")
            
        # Limit path depth for security
        if len(path.parts) > 10:
            raise ValidationError("File path too deep (max 10 levels)")
            
        return str(path)

    def upload_file(
        self, 
        file: UploadedFile, 
        file_path: str = None,
        category: str = "general",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Upload a file with RBAC enforcement.
        
        Args:
            file: Uploaded file object
            file_path: Custom file path (optional)
            category: File category for organization (e.g., 'documents', 'images')
            metadata: Additional metadata to store with the file
            
        Returns:
            Dictionary containing file information
            
        Raises:
            PermissionDenied: If user lacks upload permissions
            ValidationError: If file is invalid
        """
        # Check permissions - admins and managers can upload
        self._check_permission([OrgRole.ADMIN, OrgRole.MANAGER], "file upload")
        
        # Validate file
        if not file or not file.name:
            raise ValidationError("No file provided")
            
        # Generate file path if not provided
        if not file_path:
            file_extension = Path(file.name).suffix
            file_id = str(uuid.uuid4())
            file_path = f"{category}/{file_id}{file_extension}"
        else:
            file_path = self._validate_file_path(file_path)
            
        # Validate file size (example: 50MB limit)
        max_size = getattr(settings, 'MAX_FILE_UPLOAD_SIZE', 50 * 1024 * 1024)
        if file.size > max_size:
            raise ValidationError(f"File size ({file.size} bytes) exceeds limit ({max_size} bytes)")
            
        try:
            # Save file to storage
            saved_path = self.storage.save(file_path, file)
            
            # Generate file info
            file_info = {
                'path': saved_path,
                'original_name': file.name,
                'size': file.size,
                'content_type': getattr(file, 'content_type', 'application/octet-stream'),
                'category': category,
                'uploaded_by': self.user.id,
                'organization': self.organization.id,
                'metadata': metadata or {},
                'url': self.storage.url(saved_path)
            }
            
            logger.info(
                f"File uploaded successfully",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'file_path': saved_path,
                    'file_size': file.size,
                    'content_type': file.content_type
                }
            )
            
            return file_info
            
        except Exception as e:
            logger.error(
                f"Failed to upload file",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'file_path': file_path,
                    'error': str(e)
                }
            )
            raise

    def get_file_url(self, file_path: str, expire_seconds: int = 3600) -> str:
        """
        Get a signed URL for a file.
        
        Args:
            file_path: Path to the file
            expire_seconds: URL expiration time in seconds
            
        Returns:
            Signed URL for the file
            
        Raises:
            PermissionDenied: If user lacks access permissions
        """
        # Check permissions - all organization members can view files
        self._check_permission([OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.VIEWER], "file access")
        
        file_path = self._validate_file_path(file_path)
        
        if not self.storage.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")
            
        try:
            url = self.storage.url(file_path, expire=expire_seconds)
            
            logger.info(
                f"Generated file URL",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'file_path': file_path,
                    'expire_seconds': expire_seconds
                }
            )
            
            return url
            
        except Exception as e:
            logger.error(
                f"Failed to generate file URL",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'file_path': file_path,
                    'error': str(e)
                }
            )
            raise

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if file was deleted successfully
            
        Raises:
            PermissionDenied: If user lacks delete permissions
        """
        # Check permissions - only admins and managers can delete
        self._check_permission([OrgRole.ADMIN, OrgRole.MANAGER], "file deletion")
        
        file_path = self._validate_file_path(file_path)
        
        if not self.storage.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")
            
        try:
            self.storage.delete(file_path)
            
            logger.info(
                f"File deleted successfully",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'file_path': file_path
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to delete file",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'file_path': file_path,
                    'error': str(e)
                }
            )
            raise

    def list_files(self, directory: str = "", category: str = None) -> List[Dict[str, Any]]:
        """
        List files in a directory.
        
        Args:
            directory: Directory path to list (defaults to root)
            category: Filter by file category
            
        Returns:
            List of file information dictionaries
            
        Raises:
            PermissionDenied: If user lacks list permissions
        """
        # Check permissions - all organization members can list files
        self._check_permission([OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.VIEWER], "file listing")
        
        if directory:
            directory = self._validate_file_path(directory)
            
        # Add category filter if specified
        if category:
            directory = f"{category}/" + directory if directory else category
            
        try:
            dirs, files = self.storage.listdir(directory)
            
            file_list = []
            for file_name in files:
                full_path = f"{directory}/{file_name}".strip('/')
                try:
                    file_info = {
                        'name': file_name,
                        'path': full_path,
                        'size': self.storage.size(full_path),
                        'modified_time': self.storage.get_modified_time(full_path),
                        'url': self.storage.url(full_path)
                    }
                    file_list.append(file_info)
                except Exception as e:
                    logger.warning(f"Could not get info for file {full_path}: {e}")
                    
            logger.info(
                f"Listed files in directory",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'directory': directory,
                    'file_count': len(file_list)
                }
            )
            
            return file_list
            
        except Exception as e:
            logger.error(
                f"Failed to list files",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'directory': directory,
                    'error': str(e)
                }
            )
            raise

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file information
            
        Raises:
            PermissionDenied: If user lacks access permissions
        """
        # Check permissions - all organization members can get file info
        self._check_permission([OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.VIEWER], "file info access")
        
        file_path = self._validate_file_path(file_path)
        
        if not self.storage.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")
            
        try:
            file_info = {
                'path': file_path,
                'size': self.storage.size(file_path),
                'created_time': self.storage.get_created_time(file_path),
                'modified_time': self.storage.get_modified_time(file_path),
                'exists': True,
                'url': self.storage.url(file_path)
            }
            
            return file_info
            
        except Exception as e:
            logger.error(
                f"Failed to get file info",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'file_path': file_path,
                    'error': str(e)
                }
            )
            raise

    def get_storage_usage(self) -> Dict[str, Any]:
        """
        Get storage usage statistics for the organization.
        
        Returns:
            Dictionary containing storage usage information
            
        Raises:
            PermissionDenied: If user lacks access permissions
        """
        # Check permissions - only admins and managers can view usage stats
        self._check_permission([OrgRole.ADMIN, OrgRole.MANAGER], "storage usage access")
        
        try:
            # This is a simplified implementation
            # In a production system, you might want to cache this information
            # or maintain usage statistics in the database
            
            dirs, files = self.storage.listdir("")
            total_size = 0
            file_count = 0
            
            def calculate_directory_size(directory):
                nonlocal total_size, file_count
                dirs, files = self.storage.listdir(directory)
                
                for file_name in files:
                    file_path = f"{directory}/{file_name}".strip('/')
                    try:
                        total_size += self.storage.size(file_path)
                        file_count += 1
                    except Exception:
                        pass  # Skip files that can't be accessed
                        
                for subdir in dirs:
                    subdir_path = f"{directory}/{subdir}".strip('/')
                    calculate_directory_size(subdir_path)
            
            calculate_directory_size("")
            
            usage_info = {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'organization_id': str(self.organization.id),
                'organization_name': self.organization.name
            }
            
            logger.info(
                f"Retrieved storage usage statistics",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'total_size_bytes': total_size,
                    'file_count': file_count
                }
            )
            
            return usage_info
            
        except Exception as e:
            logger.error(
                f"Failed to get storage usage",
                extra={
                    'user_id': str(self.user.id),
                    'organization_id': str(self.organization.id),
                    'error': str(e)
                }
            )
            raise