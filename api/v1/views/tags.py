"""
ViewSets for tag-related models.

Provides CRUD operations for Tags with proper organization scoping and RBAC.
Based on the Tags Specification for global tag management.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from api.v1.views.base import BaseViewSet, BaseReadOnlyViewSet
from api.v1.serializers.tags import (
    TagSerializer,
    CreateTagSerializer,
    TagSummarySerializer,
    CreateTagSummarySerializer,
    UpdateTagSummarySerializer,
)
from constants.roles import OrgRole
from core.models import Tag


class TagViewSet(BaseViewSet):
    """
    ViewSet for Tag management.
    
    Provides CRUD operations with proper organization scoping and RBAC.
    Tags are global across the organization account and shared across all data types.
    """
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR]
    
    def get_queryset(self):
        """Filter queryset by user's organizations."""
        if not self.request.user.is_authenticated:
            return Tag.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = Tag.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'created_by')
        
        # Order by created_at desc (matching Supabase pattern)
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateTagSerializer
        return TagSerializer
    
    def get_serializer_context(self):
        """Add organization to serializer context."""
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context

    def perform_create(self, serializer):
        """Set organization and created_by when creating a tag."""
        organization = self.get_organization()
        serializer.save(
            organization=organization,
            created_by=self.request.user
        )


class TagSummaryViewSet(BaseViewSet):
    """
    ViewSet for Tag Summary management (matching Supabase API structure).
    
    This provides the tag management interface that matches the frontend expectations.
    """
    
    queryset = Tag.objects.all()
    serializer_class = TagSummarySerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR]
    
    def get_queryset(self):
        """Filter queryset by user's organizations and project."""
        if not self.request.user.is_authenticated:
            return Tag.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = Tag.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'created_by')
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        if project_id:
            # TODO: Implement proper project-scoped tag filtering
            # Since tags are now global, we could filter tags that are used by objects in that project
            pass
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        List tags with summary information.
        
        GET /api/v1/tags/
        
        Returns tag summary information matching Supabase structure.
        
        # TODO: Implement proper tag aggregation and usage counting
        This is a stub implementation.
        """
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return Response(
                {"error": _("project_id parameter is required")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Get actual tags from database and calculate usage counts
        # For now, return stub tag summaries
        stub_tags = [
            {
                "id": "tag-1-uuid",
                "title": "communication",
                "definition": "Communication related insights and facts",
                "category": "theme",
                "color": "#3B82F6",
                "status": "approved",
                "usage_count": 15,
                "project_id": project_id,
                "user_id": str(request.user.id),
                "created_at": "2024-11-20T10:00:00Z",
                "updated_at": "2024-11-20T10:00:00Z"
            },
            {
                "id": "tag-2-uuid", 
                "title": "process-improvement",
                "definition": "Process improvement opportunities",
                "category": "action",
                "color": "#10B981",
                "status": "approved",
                "usage_count": 8,
                "project_id": project_id,
                "user_id": str(request.user.id),
                "created_at": "2024-11-20T10:15:00Z",
                "updated_at": "2024-11-20T10:15:00Z"
            },
            {
                "id": "tag-3-uuid",
                "title": "user-feedback",
                "definition": "Direct feedback from users",
                "category": "source",
                "color": "#F59E0B",
                "status": "pending",
                "usage_count": 3,
                "project_id": project_id,
                "user_id": str(request.user.id),
                "created_at": "2024-11-20T11:00:00Z",
                "updated_at": "2024-11-20T11:00:00Z"
            }
        ]
        
        return Response(stub_tags)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new tag summary.
        
        POST /api/v1/tags/
        """
        serializer = CreateTagSummarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # TODO: Create actual tag record
        # For now, return stub created tag
        created_tag = {
            "id": "new-tag-uuid",
            "title": serializer.validated_data['title'],
            "definition": serializer.validated_data.get('definition', ''),
            "category": serializer.validated_data.get('category', ''),
            "color": serializer.validated_data.get('color', '#6B7280'),
            "status": serializer.validated_data.get('status', 'pending'),
            "usage_count": 0,
            "project_id": serializer.validated_data['project_id'],
            "user_id": str(request.user.id),
            "created_at": "2024-11-20T12:00:00Z",
            "updated_at": "2024-11-20T12:00:00Z"
        }
        
        return Response(created_tag, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update a tag summary.
        
        PATCH /api/v1/tags/{id}/
        """
        # TODO: Get actual tag and update it
        # For now, return stub updated tag
        
        serializer = UpdateTagSummarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_tag = {
            "id": kwargs.get('pk'),
            "title": serializer.validated_data.get('title', 'Updated Tag'),
            "definition": serializer.validated_data.get('definition', 'Updated definition'),
            "category": serializer.validated_data.get('category', 'updated'),
            "color": serializer.validated_data.get('color', '#6B7280'),
            "status": serializer.validated_data.get('status', 'approved'),
            "usage_count": 5,
            "project_id": "project-uuid",
            "user_id": str(request.user.id),
            "created_at": "2024-11-20T10:00:00Z",
            "updated_at": "2024-11-20T12:30:00Z"
        }
        
        return Response(updated_tag)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a tag summary.
        
        DELETE /api/v1/tags/{id}/
        """
        # TODO: Delete actual tag and remove from all related objects
        # This requires removing the tag from all evidence_facts, evidence_insights, etc.
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(
        detail=False,
        methods=['get'],
        url_path='usage-count',
        url_name='usage-count'
    )
    def usage_count(self, request):
        """
        Get usage count for specific tags.
        
        GET /api/v1/tags/usage-count/?project_id={project_id}&tags=["tag1","tag2"]
        
        Matches Supabase pattern for counting tag usage across tables.
        
        # TODO: Implement real tag usage counting
        This is a stub implementation.
        """
        project_id = request.query_params.get('project_id')
        tags_param = request.query_params.get('tags')
        
        if not project_id:
            return Response(
                {"error": _("project_id parameter is required")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not tags_param:
            return Response(
                {"error": _("tags parameter is required")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Parse tags parameter and count actual usage
        # Should count across evidence_facts, evidence_insights, evidence_sources.metadata.tags
        
        return Response({
            "count": 5,  # Stub count
            "message": "Stub tag usage count"
        })


class PublicTagViewSet(BaseReadOnlyViewSet):
    """
    Public read-only endpoints for Tags.
    
    Provides limited tag information accessible to any org member.
    """
    
    queryset = Tag.objects.all()
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR, OrgRole.VIEWER]
    
    def get_serializer_class(self):
        """Return minimal serializer for public access."""
        from rest_framework import serializers
        
        class PublicTagSerializer(serializers.ModelSerializer):
            class Meta:
                model = Tag
                fields = ["id", "title", "definition", "created_at"]
                read_only_fields = ["id", "title", "definition", "created_at"]
        
        return PublicTagSerializer
    
    def get_queryset(self):
        """Return tags from user's organizations."""
        if not self.request.user.is_authenticated:
            return Tag.objects.none()
        
        user_org_ids = self.request.user.organizations.values_list("id", flat=True)
        
        return Tag.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization')