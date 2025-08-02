"""
Base API views for discovery and navigation.

Provides endpoints for API discovery and navigation, allowing frontend
applications to understand available API versions and endpoints.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.urls import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    API root endpoint providing discovery information.
    
    GET /api/
    
    Returns information about available API versions and key endpoints.
    This helps frontend applications discover available API functionality.
    
    Response:
    {
        "message": "Django Backend Boilerplate API",
        "versions": {
            "v1": "/api/v1/"
        },
        "authentication": {
            "login": "/api/v1/auth/token/",
            "status": "/api/v1/auth/status/",
            "refresh": "/api/v1/auth/refresh-token/",
            "revoke": "/api/v1/auth/revoke-token/"
        },
        "docs": {
            "version": "/api/v1/version/"
        }
    }
    """
    return Response({
        'message': 'Django Backend Boilerplate API',
        'versions': {
            'v1': request.build_absolute_uri('/api/v1/')
        },
        'authentication': {
            'login': request.build_absolute_uri('/api/v1/auth/token/'),
            'status': request.build_absolute_uri('/api/v1/auth/status/'),
            'refresh': request.build_absolute_uri('/api/v1/auth/refresh-token/'),
            'revoke': request.build_absolute_uri('/api/v1/auth/revoke-token/')
        },
        'docs': {
            'version': request.build_absolute_uri('/api/v1/version/')
        }
    }, status=status.HTTP_200_OK)