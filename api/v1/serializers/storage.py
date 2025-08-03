"""
Serializers for storage API endpoints.

This module provides serializers for file upload, download, and management
operations with proper validation and data formatting.
"""

import json
from typing import Dict, Any, List

from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _


class FileUploadSerializer(serializers.Serializer):
    """
    Serializer for file upload operations.
    
    Handles file validation and metadata processing for file uploads.
    """
    
    file = serializers.FileField(
        required=True,
        help_text=_("File to upload")
    )
    
    file_path = serializers.CharField(
        required=False,
        max_length=500,
        help_text=_("Custom file path (optional)")
    )
    
    category = serializers.CharField(
        required=False,
        max_length=100,
        default='general',
        help_text=_("File category (e.g., 'documents', 'images', 'general')")
    )
    
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text=_("Additional metadata as JSON object")
    )

    def validate_file(self, value: UploadedFile) -> UploadedFile:
        """
        Validate uploaded file.
        
        Args:
            value: Uploaded file
            
        Returns:
            Validated file
            
        Raises:
            ValidationError: If file is invalid
        """
        if not value:
            raise serializers.ValidationError(_("No file provided"))
            
        if not value.name:
            raise serializers.ValidationError(_("File must have a name"))
            
        # Check file size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                _("File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)").format(
                    size=value.size,
                    max_size=max_size
                )
            )
            
        # Check for suspicious file extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.pif']
        if any(value.name.lower().endswith(ext) for ext in dangerous_extensions):
            raise serializers.ValidationError(_("File type not allowed"))
            
        return value

    def validate_file_path(self, value: str) -> str:
        """
        Validate custom file path.
        
        Args:
            value: File path
            
        Returns:
            Validated file path
            
        Raises:
            ValidationError: If path is invalid
        """
        if not value:
            return value
            
        # Check for suspicious path components
        if '..' in value or value.startswith('/'):
            raise serializers.ValidationError(_("Invalid file path"))
            
        # Limit path length
        if len(value) > 500:
            raise serializers.ValidationError(_("File path too long"))
            
        return value.strip('/')

    def validate_category(self, value: str) -> str:
        """
        Validate file category.
        
        Args:
            value: File category
            
        Returns:
            Validated category
            
        Raises:
            ValidationError: If category is invalid
        """
        if not value:
            return 'general'
            
        # Allowed categories
        allowed_categories = [
            'general', 'documents', 'images', 'videos', 'audio',
            'archives', 'spreadsheets', 'presentations', 'pdfs'
        ]
        
        if value not in allowed_categories:
            raise serializers.ValidationError(
                _("Invalid category. Allowed categories: {categories}").format(
                    categories=', '.join(allowed_categories)
                )
            )
            
        return value

    def validate_metadata(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata JSON.
        
        Args:
            value: Metadata dictionary
            
        Returns:
            Validated metadata
            
        Raises:
            ValidationError: If metadata is invalid
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Metadata must be a JSON object"))
            
        # Limit metadata size
        metadata_str = json.dumps(value)
        if len(metadata_str) > 10000:  # 10KB limit
            raise serializers.ValidationError(_("Metadata too large (max 10KB)"))
            
        return value


class FileInfoSerializer(serializers.Serializer):
    """
    Serializer for file information.
    
    Formats file metadata for API responses.
    """
    
    path = serializers.CharField(
        help_text=_("File path in storage")
    )
    
    original_name = serializers.CharField(
        required=False,
        help_text=_("Original filename when uploaded")
    )
    
    name = serializers.CharField(
        required=False,
        help_text=_("File name")
    )
    
    size = serializers.IntegerField(
        help_text=_("File size in bytes")
    )
    
    content_type = serializers.CharField(
        required=False,
        help_text=_("MIME content type")
    )
    
    category = serializers.CharField(
        required=False,
        help_text=_("File category")
    )
    
    uploaded_by = serializers.UUIDField(
        required=False,
        help_text=_("ID of user who uploaded the file")
    )
    
    organization = serializers.UUIDField(
        required=False,
        help_text=_("Organization ID")
    )
    
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text=_("Additional metadata")
    )
    
    url = serializers.URLField(
        help_text=_("Signed URL for accessing the file")
    )
    
    created_time = serializers.DateTimeField(
        required=False,
        help_text=_("File creation timestamp")
    )
    
    modified_time = serializers.DateTimeField(
        required=False,
        help_text=_("File modification timestamp")
    )
    
    exists = serializers.BooleanField(
        required=False,
        default=True,
        help_text=_("Whether the file exists")
    )


class FileListItemSerializer(serializers.Serializer):
    """
    Serializer for individual file list items.
    """
    
    name = serializers.CharField(
        help_text=_("File name")
    )
    
    path = serializers.CharField(
        help_text=_("Full file path")
    )
    
    size = serializers.IntegerField(
        help_text=_("File size in bytes")
    )
    
    modified_time = serializers.DateTimeField(
        required=False,
        help_text=_("Last modification time")
    )
    
    url = serializers.URLField(
        help_text=_("File access URL")
    )


class FileListSerializer(serializers.Serializer):
    """
    Serializer for file listing responses.
    """
    
    files = FileListItemSerializer(
        many=True,
        help_text=_("List of files")
    )


class StorageUsageSerializer(serializers.Serializer):
    """
    Serializer for storage usage statistics.
    """
    
    total_size_bytes = serializers.IntegerField(
        help_text=_("Total storage used in bytes")
    )
    
    total_size_mb = serializers.FloatField(
        help_text=_("Total storage used in megabytes")
    )
    
    file_count = serializers.IntegerField(
        help_text=_("Total number of files")
    )
    
    organization_id = serializers.UUIDField(
        help_text=_("Organization ID")
    )
    
    organization_name = serializers.CharField(
        help_text=_("Organization name")
    )


class FileDownloadResponseSerializer(serializers.Serializer):
    """
    Serializer for file download responses.
    """
    
    download_url = serializers.URLField(
        help_text=_("Signed URL for downloading the file")
    )
    
    file_path = serializers.CharField(
        help_text=_("File path in storage")
    )
    
    expires_in_seconds = serializers.IntegerField(
        help_text=_("URL expiration time in seconds")
    )