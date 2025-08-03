"""
Serializers for evidence-related models.

Provides serialization and validation for Evidence Sources, Facts, Insights,
Chunks, and Recommendations with proper organization scoping and RBAC.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from core.models import (
    EvidenceSource,
    EvidenceFact,
    EvidenceChunk,
    EvidenceInsight,
    Recommendation,
)


class EvidenceSourceSerializer(serializers.ModelSerializer):
    """
    Serializer for EvidenceSource with proper validation and organization scoping.
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    project_names = serializers.SerializerMethodField(
        help_text=_("Names of the projects this source belongs to"),
    )
    
    processing_status_display = serializers.CharField(
        source="get_processing_status_display",
        read_only=True,
        help_text=_("Human-readable processing status"),
    )
    
    type_display = serializers.CharField(
        source="get_type_display",
        read_only=True,
        help_text=_("Human-readable type"),
    )
    
    tags = serializers.SerializerMethodField(
        help_text=_("Tags associated with this evidence source")
    )
    
    class Meta:
        model = EvidenceSource
        fields = [
            "id",
            "title",
            "type",
            "type_display",
            "file_path",
            "notes",
            "file_size",
            "mime_type",
            "processing_status",
            "processing_status_display",
            "summary",
            "metadata",
            "organization",
            "organization_name",
            "projects",
            "project_names",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",  # Set automatically by viewset
            "organization_name",
            "project_names",
            "processing_status_display",
            "type_display",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        try:
            return list(obj.get_tag_names()) if hasattr(obj, "get_tag_names") else []
        except:
            return []
    
    def get_project_names(self, obj):
        """Get list of project names for this source."""
        return [project.title for project in obj.projects.all()]
    
    def validate_title(self, value):
        """Validate title field."""
        if not value or not value.strip():
            raise serializers.ValidationError(_("Title cannot be empty."))
        return value.strip()


class CreateEvidenceSourceSerializer(EvidenceSourceSerializer):
    """Serializer for creating new evidence sources."""
    
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        help_text=_("List of tag names to add to the evidence source"),
    )
    
    class Meta(EvidenceSourceSerializer.Meta):
        fields = EvidenceSourceSerializer.Meta.fields
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "type_display",
            "processing_status_display",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def create(self, validated_data):
        """Create instance with tags."""
        tags_data = validated_data.pop('tags', [])
        instance = super().create(validated_data)
        
        # Add tags
        for tag_name in tags_data:
            instance.add_tag(
                tag_name,
                instance.organization,
                self.context['request'].user
            )
        
        return instance


class EvidenceFactSerializer(serializers.ModelSerializer):
    """
    Serializer for EvidenceFact with proper validation and organization scoping.
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    project_names = serializers.SerializerMethodField(
        help_text=_("Names of the projects this fact belongs to"),
    )
    
    source_title = serializers.CharField(
        source="source.title",
        read_only=True,
        help_text=_("Title of the evidence source"),
    )
    
    sentiment_display = serializers.CharField(
        source="get_sentiment_display",
        read_only=True,
        help_text=_("Human-readable sentiment"),
    )
    
    tags = serializers.SerializerMethodField(
        help_text=_("Tags associated with this evidence fact")
    )
    
    class Meta:
        model = EvidenceFact
        fields = [
            "id",
            "title",
            "notes",
            "confidence_score",
            "participant",
            "sentiment",
            "sentiment_display",
            "embedding",
            "tags_list",
            "organization",
            "organization_name",
            "projects",
            "project_names",
            "source",
            "source_title",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "source_title",
            "sentiment_display",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        try:
            return list(obj.get_tag_names()) if hasattr(obj, "get_tag_names") else []
        except:
            return []
    
    def get_project_names(self, obj):
        """Get list of project names for this fact."""
        return [project.title for project in obj.projects.all()]


class CreateEvidenceFactSerializer(EvidenceFactSerializer):
    """Serializer for creating new evidence facts."""
    
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        help_text=_("List of tag names to add to the evidence fact"),
    )
    
    class Meta(EvidenceFactSerializer.Meta):
        fields = EvidenceFactSerializer.Meta.fields
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "source_title",
            "sentiment_display",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def create(self, validated_data):
        """Create instance with tags."""
        tags_data = validated_data.pop('tags', [])
        instance = super().create(validated_data)
        
        # Add tags
        for tag_name in tags_data:
            instance.add_tag(
                tag_name,
                instance.organization,
                self.context['request'].user
            )
        
        return instance


class BulkCreateEvidenceFactSerializer(serializers.Serializer):
    """Serializer for bulk creating evidence facts."""
    
    facts = serializers.ListField(
        child=CreateEvidenceFactSerializer(),
        help_text=_("List of evidence facts to create"),
    )
    
    def create(self, validated_data):
        """Create multiple evidence facts."""
        facts_data = validated_data['facts']
        created_facts = []
        
        for fact_data in facts_data:
            # Use the CreateEvidenceFactSerializer to create each fact
            serializer = CreateEvidenceFactSerializer(
                data=fact_data,
                context=self.context
            )
            serializer.is_valid(raise_exception=True)
            fact = serializer.save()
            created_facts.append(fact)
        
        return created_facts


class EvidenceChunkSerializer(serializers.ModelSerializer):
    """
    Serializer for EvidenceChunk with proper validation and organization scoping.
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    project_names = serializers.SerializerMethodField(
        help_text=_("Names of the projects this chunk belongs to"),
    )
    
    source_title = serializers.CharField(
        source="source.title",
        read_only=True,
        help_text=_("Title of the evidence source"),
    )
    
    class Meta:
        model = EvidenceChunk
        fields = [
            "id",
            "chunk_index",
            "chunk_text",
            "embedding",
            "metadata",
            "organization",
            "organization_name",
            "projects",
            "project_names",
            "source",
            "source_title",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "source_title",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_project_names(self, obj):
        """Get list of project names for this chunk."""
        return [project.title for project in obj.projects.all()]


class EvidenceInsightSerializer(serializers.ModelSerializer):
    """
    Serializer for EvidenceInsight with proper validation and organization scoping.
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    project_names = serializers.SerializerMethodField(
        help_text=_("Names of the projects this insight belongs to"),
    )
    
    priority_display = serializers.CharField(
        source="get_priority_display",
        read_only=True,
        help_text=_("Human-readable priority"),
    )
    
    sentiment_display = serializers.CharField(
        source="get_sentiment_display",
        read_only=True,
        help_text=_("Human-readable sentiment"),
    )
    
    evidence_level = serializers.CharField(
        read_only=True,
        help_text=_("Human-readable evidence level"),
    )
    
    tags = serializers.SerializerMethodField(
        help_text=_("Tags associated with this evidence insight")
    )
    
    supporting_evidence_count = serializers.SerializerMethodField(
        help_text=_("Number of supporting evidence facts")
    )
    
    class Meta:
        model = EvidenceInsight
        fields = [
            "id",
            "title",
            "notes",
            "priority",
            "priority_display",
            "evidence_score",
            "evidence_level",
            "sentiment",
            "sentiment_display",
            "tags_list",
            "supporting_evidence",
            "supporting_evidence_count",
            "organization",
            "organization_name",
            "projects",
            "project_names",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "priority_display",
            "sentiment_display",
            "evidence_level",
            "supporting_evidence_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        try:
            return list(obj.get_tag_names()) if hasattr(obj, "get_tag_names") else []
        except:
            return []
    
    def get_project_names(self, obj):
        """Get list of project names for this insight."""
        return [project.title for project in obj.projects.all()]
    
    def get_supporting_evidence_count(self, obj):
        """Get count of supporting evidence."""
        return obj.supporting_evidence.count()


class CreateEvidenceInsightSerializer(EvidenceInsightSerializer):
    """Serializer for creating new evidence insights."""
    
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        help_text=_("List of tag names to add to the evidence insight"),
    )
    
    class Meta(EvidenceInsightSerializer.Meta):
        fields = EvidenceInsightSerializer.Meta.fields
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "priority_display",
            "sentiment_display",
            "evidence_level",
            "supporting_evidence_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def create(self, validated_data):
        """Create instance with tags."""
        tags_data = validated_data.pop('tags', [])
        instance = super().create(validated_data)
        
        # Add tags
        for tag_name in tags_data:
            instance.add_tag(
                tag_name,
                instance.organization,
                self.context['request'].user
            )
        
        return instance


class RecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for Recommendation with proper validation and organization scoping.
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    project_names = serializers.SerializerMethodField(
        help_text=_("Names of the projects this recommendation belongs to"),
    )
    
    effort_display = serializers.CharField(
        source="get_effort_display",
        read_only=True,
        help_text=_("Human-readable effort level"),
    )
    
    impact_display = serializers.CharField(
        source="get_impact_display",
        read_only=True,
        help_text=_("Human-readable impact level"),
    )
    
    type_display = serializers.CharField(
        source="get_type_display",
        read_only=True,
        help_text=_("Human-readable type"),
    )
    
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
        help_text=_("Human-readable status"),
    )
    
    evidence_level = serializers.CharField(
        read_only=True,
        help_text=_("Human-readable evidence level"),
    )
    
    tags = serializers.SerializerMethodField(
        help_text=_("Tags associated with this recommendation")
    )
    
    supporting_evidence_count = serializers.SerializerMethodField(
        help_text=_("Number of supporting insights")
    )
    
    class Meta:
        model = Recommendation
        fields = [
            "id",
            "title",
            "notes",
            "effort",
            "effort_display",
            "impact",
            "impact_display",
            "type",
            "type_display",
            "status",
            "status_display",
            "evidence_score",
            "evidence_level",
            "tags_list",
            "supporting_evidence",
            "supporting_evidence_count",
            "organization",
            "organization_name",
            "projects",
            "project_names",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "effort_display",
            "impact_display",
            "type_display",
            "status_display",
            "evidence_level",
            "supporting_evidence_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        try:
            return list(obj.get_tag_names()) if hasattr(obj, "get_tag_names") else []
        except:
            return []
    
    def get_project_names(self, obj):
        """Get list of project names for this recommendation."""
        return [project.title for project in obj.projects.all()]
    
    def get_supporting_evidence_count(self, obj):
        """Get count of supporting evidence."""
        return obj.supporting_evidence.count()


class CreateRecommendationSerializer(RecommendationSerializer):
    """Serializer for creating new recommendations."""
    
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        help_text=_("List of tag names to add to the recommendation"),
    )
    
    class Meta(RecommendationSerializer.Meta):
        fields = RecommendationSerializer.Meta.fields
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_names",
            "effort_display",
            "impact_display",
            "type_display",
            "status_display",
            "evidence_level",
            "supporting_evidence_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def create(self, validated_data):
        """Create instance with tags."""
        tags_data = validated_data.pop('tags', [])
        instance = super().create(validated_data)
        
        # Add tags
        for tag_name in tags_data:
            instance.add_tag(
                tag_name,
                instance.organization,
                self.context['request'].user
            )
        
        return instance