"""
Version API views.

Provides endpoints for exposing application version information.
"""

import json
import os
from pathlib import Path

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


@api_view(['GET'])
@permission_classes([AllowAny])
def version_info(request):
    """
    Return application version information.
    
    Returns:
        JSON response with version info including commit, timestamp, and branch.
        If version.json doesn't exist, returns default values.
    """
    # Try to read version.json from project root
    version_file = Path(settings.BASE_DIR) / 'version.json'
    
    default_version = {
        'commit': 'unknown',
        'timestamp': 'unknown', 
        'branch': 'unknown'
    }
    
    if version_file.exists():
        try:
            with open(version_file, 'r') as f:
                version_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            version_data = default_version
    else:
        version_data = default_version
    
    return Response(version_data, status=status.HTTP_200_OK)