"""
Storage API views for file upload, download, and management with RBAC.

This module provides REST API endpoints for file operations with proper
organization-level access control and role-based permissions.
"""

import logging
from typing import Dict, Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponse, Http404
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from api.v1.serializers.storage import (
    FileUploadSerializer,
    FileInfoSerializer,
    StorageUsageSerializer,
    FileListSerializer
)
from core.services.storage import StorageService
from constants.roles import OrgRole

logger = logging.getLogger(__name__)


class StorageAPIView(viewsets.ViewSet):
    """
    API view for file storage operations with RBAC enforcement.
    
    Provides endpoints for uploading, downloading, listing, and managing files
    with proper organization-level access control.
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_organization(self):
        """
        Get the organization context for this request.
        
        Returns:
            Organization: The organization for this request context
        """
        # Try to get organization from URL parameters first
        org_id = self.kwargs.get("organization_id") or self.kwargs.get("org_id")
        if org_id:
            try:
                from core.models import Organization
                return Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                return None

        # Fall back to user's default organization
        if hasattr(self.request, "user") and self.request.user.is_authenticated:
            return self.request.user.get_default_organization()

        return None

    def get_storage_service(self) -> StorageService:
        """
        Get storage service instance for the current user and organization.
        
        Returns:
            StorageService instance
            
        Raises:
            ValidationError: If organization context is missing
        """
        organization = self.get_organization()
        if not organization:
            raise ValidationError(_("Organization context is required for storage operations"))
            
        return StorageService(user=self.request.user, organization=organization)

    def upload_file(self, request):
        """
        Upload a file to organization storage.
        
        POST /api/v1/storage/upload/
        
        Request format:
        - Content-Type: multipart/form-data
        - file: File to upload
        - category: File category (optional, default: 'general')
        - file_path: Custom file path (optional)
        - metadata: Additional metadata as JSON string (optional)
        
        Returns:
            201: File uploaded successfully
            400: Invalid request or file
            403: Insufficient permissions
            413: File too large
        """
        try:
            serializer = FileUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            storage_service = self.get_storage_service()
            
            # Upload file using storage service
            file_info = storage_service.upload_file(
                file=serializer.validated_data['file'],
                file_path=serializer.validated_data.get('file_path'),
                category=serializer.validated_data.get('category', 'general'),
                metadata=serializer.validated_data.get('metadata', {})
            )
            
            # Return file information
            response_serializer = FileInfoSerializer(file_info)
            
            return Response(
                {
                    'message': _('File uploaded successfully'),
                    'file': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in file upload: {e}")
            return Response(
                {'error': _('An unexpected error occurred during file upload')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def download_file(self, request, file_path=None):
        """
        Get a signed URL for downloading a file.
        
        GET /api/v1/storage/download/{file_path}/
        
        Query parameters:
        - expire: URL expiration time in seconds (optional, default: 3600)
        
        Returns:
            200: Signed URL for file download
            404: File not found
            403: Insufficient permissions
        """
        if not file_path:
            return Response(
                {'error': _('File path is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            storage_service = self.get_storage_service()
            expire_seconds = int(request.query_params.get('expire', 3600))
            
            # Get signed URL for file
            signed_url = storage_service.get_file_url(
                file_path=file_path,
                expire_seconds=expire_seconds
            )
            
            return Response({
                'download_url': signed_url,
                'file_path': file_path,
                'expires_in_seconds': expire_seconds
            })
            
        except ValidationError as e:
            if "not found" in str(e).lower():
                return Response(
                    {'error': _('File not found')},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Unexpected error in file download: {e}")
            return Response(
                {'error': _('An unexpected error occurred during file download')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete_file(self, request, file_path=None):
        """
        Delete a file from storage.
        
        DELETE /api/v1/storage/delete/{file_path}/
        
        Returns:
            204: File deleted successfully
            404: File not found
            403: Insufficient permissions
        """
        if not file_path:
            return Response(
                {'error': _('File path is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            storage_service = self.get_storage_service()
            
            # Delete file
            storage_service.delete_file(file_path)
            
            return Response(
                {'message': _('File deleted successfully')},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except ValidationError as e:
            if "not found" in str(e).lower():
                return Response(
                    {'error': _('File not found')},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Unexpected error in file deletion: {e}")
            return Response(
                {'error': _('An unexpected error occurred during file deletion')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list_files(self, request):
        """
        List files in a directory.
        
        GET /api/v1/storage/list/
        
        Query parameters:
        - directory: Directory path to list (optional, default: root)
        - category: Filter by file category (optional)
        
        Returns:
            200: List of files with metadata
            403: Insufficient permissions
        """
        try:
            storage_service = self.get_storage_service()
            
            directory = request.query_params.get('directory', '')
            category = request.query_params.get('category')
            
            # List files
            files = storage_service.list_files(
                directory=directory,
                category=category
            )
            
            serializer = FileListSerializer({'files': files})
            
            return Response(serializer.data)
            
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Unexpected error in file listing: {e}")
            return Response(
                {'error': _('An unexpected error occurred during file listing')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_file_info(self, request, file_path=None):
        """
        Get detailed information about a file.
        
        GET /api/v1/storage/info/{file_path}/
        
        Returns:
            200: File information
            404: File not found
            403: Insufficient permissions
        """
        if not file_path:
            return Response(
                {'error': _('File path is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            storage_service = self.get_storage_service()
            
            # Get file info
            file_info = storage_service.get_file_info(file_path)
            
            serializer = FileInfoSerializer(file_info)
            
            return Response(serializer.data)
            
        except ValidationError as e:
            if "not found" in str(e).lower():
                return Response(
                    {'error': _('File not found')},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Unexpected error in get file info: {e}")
            return Response(
                {'error': _('An unexpected error occurred while getting file info')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_storage_usage(self, request):
        """
        Get storage usage statistics for the organization.
        
        GET /api/v1/storage/usage/
        
        Returns:
            200: Storage usage information
            403: Insufficient permissions
        """
        try:
            storage_service = self.get_storage_service()
            
            # Get storage usage
            usage_info = storage_service.get_storage_usage()
            
            serializer = StorageUsageSerializer(usage_info)
            
            return Response(serializer.data)
            
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Unexpected error in get storage usage: {e}")
            return Response(
                {'error': _('An unexpected error occurred while getting storage usage')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# For compatibility with existing URL patterns
storage_upload = StorageAPIView.as_view()
storage_download = StorageAPIView.as_view()
storage_delete = StorageAPIView.as_view()
storage_list = StorageAPIView.as_view()
storage_info = StorageAPIView.as_view()
storage_usage = StorageAPIView.as_view()