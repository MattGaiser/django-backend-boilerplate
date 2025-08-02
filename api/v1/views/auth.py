"""
Authentication-related API views.

Provides endpoints for token-based authentication and session management.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from core.models import User


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError(
                    _("Unable to log in with provided credentials.")
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    _("User account is disabled.")
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                _("Must include email and password.")
            )


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for authentication token with user information.
    """
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Token
        fields = ['key', 'user', 'created']
        read_only_fields = ['key', 'created']
    
    def get_user(self, obj):
        """
        Return basic user information with the token.
        """
        from api.v1.serializers.user import UserWithOrganizationsSerializer
        return UserWithOrganizationsSerializer(obj.user).data


@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_auth_token(request):
    """
    Obtain an authentication token for a user.
    
    POST /api/v1/auth/token/
    
    Body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "key": "token_string",
        "user": {
            "id": "uuid",
            "email": "user@example.com",
            "full_name": "User Name",
            ...
        },
        "created": "2023-01-01T00:00:00Z"
    }
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Get or create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        # Update user's last login IP if available
        user_ip = request.META.get('REMOTE_ADDR')
        if user_ip and hasattr(user, 'last_login_ip'):
            user.last_login_ip = user_ip
            user.save(update_fields=['last_login_ip'])
        
        # Serialize token response
        token_serializer = TokenSerializer(token)
        
        return Response(token_serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_auth_token(request):
    """
    Revoke the current user's authentication token.
    
    POST /api/v1/auth/revoke-token/
    
    This will invalidate the current token, requiring the user to log in again.
    """
    try:
        # Get the user's token and delete it
        token = Token.objects.get(user=request.user)
        token.delete()
        
        return Response(
            {'message': _("Token revoked successfully.")},
            status=status.HTTP_200_OK
        )
    except Token.DoesNotExist:
        return Response(
            {'message': _("No active token found.")},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_auth_token(request):
    """
    Refresh the current user's authentication token.
    
    POST /api/v1/auth/refresh-token/
    
    This will generate a new token and invalidate the old one.
    """
    try:
        # Get the user's existing token and delete it
        old_token = Token.objects.get(user=request.user)
        old_token.delete()
    except Token.DoesNotExist:
        # No existing token, which is fine
        pass
    
    # Create a new token
    new_token = Token.objects.create(user=request.user)
    
    # Serialize token response
    token_serializer = TokenSerializer(new_token)
    
    return Response(token_serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def token_info(request):
    """
    Get information about the current authentication token.
    
    GET /api/v1/auth/token-info/
    
    Returns information about the currently used token including
    when it was created and associated user information.
    """
    try:
        token = Token.objects.get(user=request.user)
        token_serializer = TokenSerializer(token)
        
        return Response(token_serializer.data, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response(
            {'message': _("No active token found.")},
            status=status.HTTP_404_NOT_FOUND
        )