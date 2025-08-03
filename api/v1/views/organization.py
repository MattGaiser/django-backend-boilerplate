"""
ViewSets for organization and project models.

Provides CRUD operations for Organizations, Projects, and Organization Memberships
with proper RBAC and multi-tenant support.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from api.v1.views.base import BaseViewSet, BaseReadOnlyViewSet
from api.v1.serializers.organization import (
    OrganizationSerializer,
    CreateOrganizationSerializer,
    ProjectSerializer,
    CreateProjectSerializer,
    OrganizationMembershipSerializer,
    OrganizationMembershipListSerializer,
)
from constants.roles import OrgRole
from core.models import Organization, Project, OrganizationMembership


class OrganizationViewSet(BaseViewSet):
    """
    ViewSet for Organization management.
    
    Provides CRUD operations with proper RBAC.
    Users can only see organizations they are members of.
    """
    
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    required_roles = []  # Custom permission logic below
    
    def get_queryset(self):
        """Filter queryset by user's organization memberships."""
        if not self.request.user.is_authenticated:
            return Organization.objects.none()
        
        # Users can see organizations they are members of
        user_org_ids = self.request.user.organizations.values_list("id", flat=True)
        return Organization.objects.filter(id__in=user_org_ids)
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateOrganizationSerializer
        return OrganizationSerializer
    
    def perform_create(self, serializer):
        """
        Create organization and add creator as admin.
        """
        organization = serializer.save(created_by=self.request.user)
        
        # Create membership for the creator as admin
        OrganizationMembership.objects.create(
            user=self.request.user,
            organization=organization,
            role=OrgRole.ADMIN,
            is_default=True,  # First org becomes default
            created_by=self.request.user
        )
    
    def get_permissions(self):
        """
        Custom permissions for organization operations.
        
        - List/Retrieve: Any authenticated user can see their orgs
        - Create: Any authenticated user can create orgs
        - Update/Delete: Only admins of the organization
        """
        from rest_framework.permissions import IsAuthenticated
        from api.v1.permissions import IsOwnerOrAdmin
        
        if self.action in ['create', 'list']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['retrieve']:
            permission_classes = [IsAuthenticated]
        else:  # update, partial_update, destroy
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        
        return [permission() for permission in permission_classes]


class OrganizationMembershipViewSet(BaseViewSet):
    """
    ViewSet for OrganizationMembership management.
    
    Provides operations for managing organization memberships with proper RBAC.
    """
    
    queryset = OrganizationMembership.objects.all()
    serializer_class = OrganizationMembershipSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER]
    
    def get_queryset(self):
        """Filter queryset by user's organizations."""
        if not self.request.user.is_authenticated:
            return OrganizationMembership.objects.none()
        
        # Users can see memberships for organizations they have admin/manager access to
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        return OrganizationMembership.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('user', 'organization', 'created_by')
    
    @action(
        detail=False,
        methods=['get'],
        url_path='user-orgs',
        url_name='user-orgs'
    )
    def user_organizations(self, request):
        """
        Get organizations for the current user (matching Supabase pattern).
        
        GET /api/v1/organization-memberships/user-orgs/
        
        Returns organizations via memberships similar to Supabase:
        organization_memberships?select=organization:organizations(*)&user_id=eq.{user_id}
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": _("Authentication required.")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        memberships = OrganizationMembership.objects.filter(
            user=request.user
        ).select_related('organization')
        
        serializer = OrganizationMembershipListSerializer(
            memberships,
            many=True,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['get'],
        url_path='user-role',
        url_name='user-role'
    )
    def user_role(self, request):
        """
        Get user role in a specific organization.
        
        GET /api/v1/organization-memberships/user-role/?organization_id={org_id}
        
        Returns role similar to Supabase:
        organization_memberships?organization_id=eq.{org_id}&user_id=eq.{user_id}&select=role
        """
        organization_id = request.query_params.get('organization_id')
        
        if not organization_id:
            return Response(
                {"error": _("organization_id parameter is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            membership = OrganizationMembership.objects.get(
                user=request.user,
                organization_id=organization_id
            )
            return Response({"role": membership.role})
        except OrganizationMembership.DoesNotExist:
            return Response(
                {"error": _("User is not a member of this organization.")},
                status=status.HTTP_404_NOT_FOUND
            )


class ProjectViewSet(BaseViewSet):
    """
    ViewSet for Project management.
    
    Provides CRUD operations with proper organization scoping and RBAC.
    """
    
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR]
    
    def get_queryset(self):
        """Filter queryset by user's organizations."""
        if not self.request.user.is_authenticated:
            return Project.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = Project.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'created_by')
        
        # Filter by organization if specified
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateProjectSerializer
        return ProjectSerializer
    
    def get_serializer_context(self):
        """Add organization to serializer context."""
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context
    
    @action(
        detail=True,
        methods=['post'],
        url_path='add-tag',
        url_name='add-tag'
    )
    def add_tag(self, request, pk=None):
        """
        Add a tag to the project.
        
        POST /api/v1/projects/{id}/add-tag/
        Body: {"name": "tag-name"}
        """
        instance = self.get_object()
        tag_name = request.data.get('name')
        
        if not tag_name:
            return Response(
                {"error": _("Tag name is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tag = instance.add_tag(
                tag_name,
                instance.organization,
                request.user
            )
            return Response({
                "message": _("Tag added successfully."),
                "tag": {"name": tag.name, "id": str(tag.id)}
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(
        detail=True,
        methods=['delete'],
        url_path='remove-tag',
        url_name='remove-tag'
    )
    def remove_tag(self, request, pk=None):
        """
        Remove a tag from the project.
        
        DELETE /api/v1/projects/{id}/remove-tag/
        Body: {"name": "tag-name"}
        """
        instance = self.get_object()
        tag_name = request.data.get('name')
        
        if not tag_name:
            return Response(
                {"error": _("Tag name is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        removed = instance.remove_tag(tag_name, instance.organization)
        
        if removed:
            return Response({"message": _("Tag removed successfully.")})
        else:
            return Response(
                {"error": _("Tag not found.")},
                status=status.HTTP_404_NOT_FOUND
            )


class PublicProjectViewSet(BaseReadOnlyViewSet):
    """
    Public read-only endpoints for Project.
    
    Provides limited information accessible to any org member.
    """
    
    queryset = Project.objects.filter(is_active=True)
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR, OrgRole.VIEWER]
    
    def get_serializer_class(self):
        """Return minimal serializer for public access."""
        from rest_framework import serializers
        
        class PublicProjectSerializer(serializers.ModelSerializer):
            organization_name = serializers.CharField(
                source="organization.name",
                read_only=True
            )
            
            class Meta:
                model = Project
                fields = [
                    "id",
                    "name",
                    "description",
                    "status",
                    "organization",
                    "organization_name",
                    "created_at"
                ]
                read_only_fields = [
                    "id",
                    "name",
                    "description",
                    "status",
                    "organization",
                    "organization_name",
                    "created_at"
                ]
        
        return PublicProjectSerializer
    
    def get_queryset(self):
        """Return projects from user's organizations."""
        if not self.request.user.is_authenticated:
            return Project.objects.none()
        
        user_org_ids = self.request.user.organizations.values_list("id", flat=True)
        
        return Project.objects.filter(
            organization_id__in=user_org_ids,
            is_active=True
        ).select_related('organization')