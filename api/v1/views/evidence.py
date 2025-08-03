"""
ViewSets for evidence-related models.

Provides CRUD operations for Evidence Sources, Facts, Insights, Chunks,
and Recommendations with proper organization scoping and RBAC.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from api.v1.views.base import BaseViewSet, BaseReadOnlyViewSet
from api.v1.serializers.evidence import (
    EvidenceSourceSerializer,
    CreateEvidenceSourceSerializer,
    EvidenceFactSerializer,
    CreateEvidenceFactSerializer,
    BulkCreateEvidenceFactSerializer,
    EvidenceChunkSerializer,
    EvidenceInsightSerializer,
    CreateEvidenceInsightSerializer,
    RecommendationSerializer,
    CreateRecommendationSerializer,
)
from constants.roles import OrgRole
from core.models import (
    EvidenceSource,
    EvidenceFact,
    EvidenceChunk,
    EvidenceInsight,
    Recommendation,
)


class EvidenceSourceViewSet(BaseViewSet):
    """
    ViewSet for EvidenceSource management.
    
    Provides CRUD operations with proper organization scoping and RBAC.
    """
    
    queryset = EvidenceSource.objects.all()
    serializer_class = EvidenceSourceSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR]
    
    def get_queryset(self):
        """Filter queryset by user's organizations and project."""
        if not self.request.user.is_authenticated:
            return EvidenceSource.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = EvidenceSource.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'created_by').prefetch_related('projects')
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(projects__id=project_id)
        
        # Order by created_at desc (since upload_date field was removed)
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateEvidenceSourceSerializer
        return EvidenceSourceSerializer
    
    def get_serializer_context(self):
        """Add organization to serializer context."""
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context
    
    @action(
        detail=True,
        methods=['patch'],
        url_path='status',
        url_name='update-status'
    )
    def update_status(self, request, pk=None):
        """
        Update processing status of evidence source.
        
        PATCH /api/v1/evidence-sources/{id}/status/
        Body: {"processing_status": "pending|processing|completed|failed"}
        """
        instance = self.get_object()
        processing_status = request.data.get('processing_status')
        
        if not processing_status:
            return Response(
                {"error": _("Processing status is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if processing_status not in [choice[0] for choice in EvidenceSource.ProcessingStatusChoices.choices]:
            return Response(
                {"error": _("Invalid processing status.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.processing_status = processing_status
        instance.save(update_fields=['processing_status'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['patch'],
        url_path='metadata',
        url_name='update-metadata'
    )
    def update_metadata(self, request, pk=None):
        """
        Update metadata (including tags) of evidence source.
        
        PATCH /api/v1/evidence-sources/{id}/metadata/
        Body: {"metadata": {"tags": ["tag1", "tag2"]}}
        """
        instance = self.get_object()
        metadata = request.data.get('metadata', {})
        
        # TODO: Implement real metadata update logic
        # For now, just update the metadata field
        instance.metadata.update(metadata)
        instance.save(update_fields=['metadata'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class EvidenceFactViewSet(BaseViewSet):
    """
    ViewSet for EvidenceFact management.
    
    Provides CRUD operations with proper organization scoping and RBAC.
    """
    
    queryset = EvidenceFact.objects.all()
    serializer_class = EvidenceFactSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR]
    
    def get_queryset(self):
        """Filter queryset by user's organizations and project."""
        if not self.request.user.is_authenticated:
            return EvidenceFact.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = EvidenceFact.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'source', 'created_by').prefetch_related('projects')
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(projects__id=project_id)
        
        # Filter by source if specified
        source_id = self.request.query_params.get('source_id')
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        
        # Order by created_at desc (since extracted_at field was removed)
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateEvidenceFactSerializer
        elif self.action == 'bulk_create':
            return BulkCreateEvidenceFactSerializer
        return EvidenceFactSerializer
    
    def get_serializer_context(self):
        """Add organization to serializer context."""
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context
    
    @action(
        detail=False,
        methods=['post'],
        url_path='bulk',
        url_name='bulk-create'
    )
    def bulk_create(self, request):
        """
        Bulk create evidence facts.
        
        POST /api/v1/evidence-facts/bulk/
        Body: [{"source_id": "uuid", "content": "...", ...}, ...]
        """
        # Convert single list to the expected format
        facts_data = request.data
        if isinstance(facts_data, list):
            request.data = {"facts": facts_data}
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        facts = serializer.save()
        
        # Return serialized facts
        output_serializer = EvidenceFactSerializer(facts, many=True, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(
        detail=True,
        methods=['patch'],
        url_path='tags',
        url_name='update-tags'
    )
    def update_tags(self, request, pk=None):
        """
        Update tags of evidence fact.
        
        PATCH /api/v1/evidence-facts/{id}/tags/
        Body: {"tags": ["tag1", "tag2"]}
        """
        instance = self.get_object()
        tags = request.data.get('tags', [])
        
        # TODO: Implement real tag update logic
        instance.tags_list = tags
        instance.save(update_fields=['tags_list'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['patch'],
        url_path='embedding',
        url_name='update-embedding'
    )
    def update_embedding(self, request, pk=None):
        """
        Update embedding of evidence fact.
        
        PATCH /api/v1/evidence-facts/{id}/embedding/
        Body: {"embedding": "[0.1,0.2,0.3,...]"}
        """
        instance = self.get_object()
        embedding = request.data.get('embedding')
        
        if not embedding:
            return Response(
                {"error": _("Embedding is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.embedding = embedding
        instance.save(update_fields=['embedding'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class EvidenceChunkViewSet(BaseReadOnlyViewSet):
    """
    ViewSet for EvidenceChunk (read-only).
    
    Evidence chunks are created automatically by the system during document processing.
    """
    
    queryset = EvidenceChunk.objects.all()
    serializer_class = EvidenceChunkSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR, OrgRole.VIEWER]
    
    def get_queryset(self):
        """Filter queryset by user's organizations."""
        if not self.request.user.is_authenticated:
            return EvidenceChunk.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = EvidenceChunk.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'source', 'created_by').prefetch_related('projects')
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(projects__id=project_id)
        
        return queryset.order_by('source_id', 'chunk_index')


class EvidenceInsightViewSet(BaseViewSet):
    """
    ViewSet for EvidenceInsight management.
    
    Provides CRUD operations with proper organization scoping and RBAC.
    """
    
    queryset = EvidenceInsight.objects.all()
    serializer_class = EvidenceInsightSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR]
    
    def get_queryset(self):
        """Filter queryset by user's organizations and project."""
        if not self.request.user.is_authenticated:
            return EvidenceInsight.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = EvidenceInsight.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'created_by').prefetch_related('supporting_evidence', 'projects')
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(projects__id=project_id)
        
        # Order by created_at desc (matching Supabase pattern)
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateEvidenceInsightSerializer
        return EvidenceInsightSerializer
    
    def get_serializer_context(self):
        """Add organization to serializer context."""
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context
    
    @action(
        detail=True,
        methods=['patch'],
        url_path='tags',
        url_name='update-tags'
    )
    def update_tags(self, request, pk=None):
        """
        Update tags of evidence insight.
        
        PATCH /api/v1/evidence-insights/{id}/tags/
        Body: {"tags": ["tag1", "tag2"]}
        """
        instance = self.get_object()
        tags = request.data.get('tags', [])
        
        # TODO: Implement real tag update logic
        instance.tags_list = tags
        instance.save(update_fields=['tags_list'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class RecommendationViewSet(BaseViewSet):
    """
    ViewSet for Recommendation management.
    
    Provides CRUD operations with proper organization scoping and RBAC.
    """
    
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER, OrgRole.EDITOR]
    
    def get_queryset(self):
        """Filter queryset by user's organizations and project."""
        if not self.request.user.is_authenticated:
            return Recommendation.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        queryset = Recommendation.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'created_by').prefetch_related('supporting_evidence', 'projects')
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(projects__id=project_id)
        
        # Order by created_at desc (matching Supabase pattern)
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateRecommendationSerializer
        return RecommendationSerializer
    
    def get_serializer_context(self):
        """Add organization to serializer context."""
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context