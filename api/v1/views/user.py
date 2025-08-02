"""
User-related API views.

Provides endpoints for user profile management and authentication.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from core.models import User
from api.v1.views.base import BaseViewSet, BaseReadOnlyViewSet
from api.v1.serializers.user import (
    UserProfileSerializer, 
    UserWithOrganizationsSerializer,
    CreateUserSerializer
)
from constants.roles import OrgRole


class UserViewSet(BaseViewSet):
    """
    ViewSet for user management.
    
    Provides CRUD operations for users with proper organization scoping.
    Most operations require admin privileges within the organization.
    """
    
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    required_roles = [OrgRole.ADMIN]  # Only admins can manage users
    
    def get_queryset(self):
        """
        Get users filtered by organization.
        
        Returns users that belong to the same organizations as the requesting user.
        """
        if not self.request.user.is_authenticated:
            return User.objects.none()
        
        # Get organizations where the user has admin access
        user_org_ids = self.request.user.organization_memberships.filter(
            role=OrgRole.ADMIN
        ).values_list('organization_id', flat=True)
        
        # Return users who are members of those organizations
        return User.objects.filter(
            organizations__id__in=user_org_ids
        ).distinct()
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'create':
            return CreateUserSerializer
        elif self.action == 'me':
            return UserWithOrganizationsSerializer
        return UserProfileSerializer
    
    @action(
        detail=False, 
        methods=['get', 'patch'], 
        permission_classes=[IsAuthenticated],
        url_path='me',
        url_name='me'
    )
    def me(self, request):
        """
        Get or update the current user's profile.
        
        GET /api/v1/me/
        Returns the current user's profile information including organizations.
        
        PATCH /api/v1/me/
        Updates the current user's profile information.
        
        This endpoint does not require organization-level permissions since
        users should always be able to view and update their own profile.
        """
        if request.method == 'GET':
            serializer = UserWithOrganizationsSerializer(request.user)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = UserProfileSerializer(
                request.user, 
                data=request.data, 
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                
                # Return updated data with organizations
                response_serializer = UserWithOrganizationsSerializer(request.user)
                return Response(response_serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='change-password',
        url_name='change-password'
    )
    def change_password(self, request):
        """
        Change the current user's password.
        
        POST /api/v1/me/change-password/
        
        Requires:
        - current_password: The user's current password
        - new_password: The new password
        - new_password_confirm: Confirmation of the new password
        """
        from rest_framework import serializers
        
        # Define inline serializer for password change
        class ChangePasswordSerializer(serializers.Serializer):
            current_password = serializers.CharField(required=True)
            new_password = serializers.CharField(required=True, min_length=8)
            new_password_confirm = serializers.CharField(required=True)
            
            def validate(self, attrs):
                if attrs['new_password'] != attrs['new_password_confirm']:
                    raise serializers.ValidationError({
                        'new_password_confirm': _("New passwords do not match.")
                    })
                return attrs
        
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check current password
            if not request.user.check_password(serializer.validated_data['current_password']):
                return Response(
                    {'current_password': [_("Current password is incorrect.")]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            return Response(
                {'message': _("Password changed successfully.")},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserViewSet(BaseReadOnlyViewSet):
    """
    Public read-only user endpoints.
    
    Provides limited user information that can be accessed without
    organization-specific permissions.
    """
    
    queryset = User.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return a minimal user serializer for public access.
        """
        from rest_framework import serializers
        
        class PublicUserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['id', 'full_name', 'date_joined']
                read_only_fields = ['id', 'full_name', 'date_joined']
        
        return PublicUserSerializer
    
    def get_queryset(self):
        """
        Return users that are in the same organizations as the requesting user.
        """
        if not self.request.user.is_authenticated:
            return User.objects.none()
        
        # Get organizations the user belongs to
        user_org_ids = self.request.user.organizations.values_list('id', flat=True)
        
        # Return users who are members of the same organizations
        return User.objects.filter(
            organizations__id__in=user_org_ids,
            is_active=True
        ).distinct()