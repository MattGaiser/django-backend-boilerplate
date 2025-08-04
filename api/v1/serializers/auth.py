"""
Serializers for authentication endpoints.

Provides serialization and validation for authentication operations
matching the Supabase API structure.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from core.models import User


class SignUpSerializer(serializers.Serializer):
    """
    Serializer for user registration (signup).
    """
    
    email = serializers.EmailField(
        help_text=_("Email address for the new account")
    )
    
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        help_text=_("Password for the new account")
    )
    
    options = serializers.DictField(
        required=False,
        help_text=_("Additional options for signup")
    )
    
    def validate_email(self, value):
        """Validate that email is not already in use."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()
    
    def validate_options(self, value):
        """Validate options field."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                _("Options must be a dictionary.")
            )
        return value
    
    def create(self, validated_data):
        """Create a new user account."""
        email = validated_data['email']
        password = validated_data['password']
        options = validated_data.get('options', {})
        
        # Extract full_name from options.data
        data = options.get('data', {})
        full_name = data.get('full_name', '')
        
        # If no full_name provided, use part of email
        if not full_name:
            full_name = email.split('@')[0]
        
        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password=password
        )
        
        return user


class SignInSerializer(serializers.Serializer):
    """
    Serializer for user authentication (signin).
    """
    
    email = serializers.EmailField(
        help_text=_("Email address")
    )
    
    password = serializers.CharField(
        write_only=True,
        help_text=_("Password")
    )
    
    def validate(self, attrs):
        """Validate email and password combination."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    _("Invalid email or password.")
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


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user session information.
    """
    
    user_metadata = serializers.SerializerMethodField(
        help_text=_("User metadata information")
    )
    
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "user_metadata",
        ]
        read_only_fields = [
            "id",
            "email",
            "user_metadata",
        ]
    
    def get_user_metadata(self, obj):
        """Get user metadata matching Supabase format."""
        return {
            "full_name": obj.full_name,
        }


class AuthResponseSerializer(serializers.Serializer):
    """
    Serializer for authentication response (matching Supabase format).
    """
    
    user = UserSessionSerializer(
        read_only=True,
        help_text=_("User information")
    )
    
    session = serializers.SerializerMethodField(
        help_text=_("Session information")
    )
    
    def get_session(self, obj):
        """
        Get session information.
        
        # TODO: Implement real JWT token generation
        This is a stub implementation.
        """
        return {
            "access_token": "stub_access_token_12345",
            "refresh_token": "stub_refresh_token_12345",
            "expires_in": 3600,
            "token_type": "bearer"
        }


class TokenInfoSerializer(serializers.Serializer):
    """
    Serializer for token information endpoint.
    """
    
    user_id = serializers.UUIDField(
        read_only=True,
        help_text=_("ID of the authenticated user")
    )
    
    email = serializers.EmailField(
        read_only=True,
        help_text=_("Email of the authenticated user")
    )
    
    expires_at = serializers.DateTimeField(
        read_only=True,
        help_text=_("When the token expires")
    )
    
    token_type = serializers.CharField(
        read_only=True,
        default="bearer",
        help_text=_("Type of token")
    )


class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer for token refresh requests.
    """
    
    refresh_token = serializers.CharField(
        write_only=True,
        help_text=_("Refresh token to exchange for new access token")
    )
    
    def validate_refresh_token(self, value):
        """
        Validate refresh token.
        
        # TODO: Implement real refresh token validation
        This is a stub implementation.
        """
        if not value:
            raise serializers.ValidationError(
                _("Refresh token is required.")
            )
        return value