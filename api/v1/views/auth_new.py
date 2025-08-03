"""
Authentication views matching Supabase API structure.

Provides signup, signin, signout, and session management endpoints
that match the expected Supabase API format.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.utils.translation import gettext_lazy as _

from api.v1.serializers.auth import (
    SignUpSerializer,
    SignInSerializer,
    AuthResponseSerializer,
    UserSessionSerializer,
    TokenInfoSerializer,
    RefreshTokenSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """
    User registration endpoint.
    
    POST /api/v1/auth/signup/
    
    Matches Supabase: POST /auth/v1/signup
    """
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.save()
    
    # Log the user in with explicit backend
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    # Return response in Supabase format
    response_data = {
        'user': user,
        'session': {}  # Will be populated by AuthResponseSerializer
    }
    
    response_serializer = AuthResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signin(request):
    """
    User authentication endpoint.
    
    POST /api/v1/auth/signin/
    
    Matches Supabase: POST /auth/v1/token?grant_type=password
    """
    serializer = SignInSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    
    # Log the user in with explicit backend
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    # Return response in Supabase format
    response_data = {
        'user': user,
        'session': {}  # Will be populated by AuthResponseSerializer
    }
    
    response_serializer = AuthResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def signout(request):
    """
    User logout endpoint.
    
    POST /api/v1/auth/signout/
    
    Matches Supabase: POST /auth/v1/logout
    """
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session(request):
    """
    Get current user session.
    
    GET /api/v1/auth/session/
    
    Matches Supabase: GET /auth/v1/user
    """
    serializer = UserSessionSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token.
    
    POST /api/v1/auth/refresh-token/
    
    # TODO: Implement real JWT refresh token logic
    This is a stub implementation.
    """
    serializer = RefreshTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # TODO: Validate refresh token and generate new access token
    response_data = {
        "access_token": "new_stub_access_token_12345",
        "refresh_token": "new_stub_refresh_token_12345",
        "expires_in": 3600,
        "token_type": "bearer"
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def token_info(request):
    """
    Get information about the current token.
    
    GET /api/v1/auth/token-info/
    """
    from django.utils import timezone
    
    # TODO: Implement real token info extraction
    # For now, return stub data based on user
    data = {
        "user_id": request.user.id,
        "email": request.user.email,
        "expires_at": timezone.now() + timezone.timedelta(hours=1),
        "token_type": "bearer"
    }
    
    serializer = TokenInfoSerializer(data)
    return Response(serializer.data)