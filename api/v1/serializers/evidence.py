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
    
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        help_text=_("Name of the project"),
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
            "name",
            "type",
            "type_display",
            "file_path",
            "content",
            "file_size",
            "mime_type",
            "processing_status",
            "processing_status_display",
            "upload_date",
            "summary",
            "notes",
            "metadata",
            "organization",
            "organization_name",
            "project",
            "project_name",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_name",
            "type_display",
            "processing_status_display",
            "upload_date",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        return list(obj.get_tag_names())
    
    def validate_name(self, value):
        """Validate name field."""
        if not value or not value.strip():
            raise serializers.ValidationError(_("Name cannot be empty."))
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
            "project_name",
            "type_display",
            "processing_status_display",
            "upload_date",
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
    
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        help_text=_("Name of the project"),
    )
    
    source_name = serializers.CharField(
        source="source.name",
        read_only=True,
        help_text=_("Name of the evidence source"),
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
            "content",
            "title",
            "notes",
            "confidence_score",
            "participant",
            "sentiment",
            "sentiment_display",
            "extracted_at",
            "embedding",
            "tags_list",
            "organization",
            "organization_name",
            "project",
            "project_name",
            "source",
            "source_name",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_name",
            "source_name",
            "sentiment_display",
            "extracted_at",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        return list(obj.get_tag_names())


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
            "project_name",
            "source_name",
            "sentiment_display",
            "extracted_at",
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
    
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        help_text=_("Name of the project"),
    )
    
    source_name = serializers.CharField(
        source="source.name",
        read_only=True,
        help_text=_("Name of the evidence source"),
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
            "project",
            "project_name",
            "source",
            "source_name",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_name",
            "source_name",
            "created_at",
            "updated_at",
            "created_by",
        ]


class EvidenceInsightSerializer(serializers.ModelSerializer):
    """
    Serializer for EvidenceInsight with proper validation and organization scoping.
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        help_text=_("Name of the project"),
    )
    
    priority_display = serializers.CharField(
        source="get_priority_display",
        read_only=True,
        help_text=_("Human-readable priority"),
    )
    
    tags = serializers.SerializerMethodField(
        help_text=_("Tags associated with this evidence insight")
    )
    
    related_facts_count = serializers.SerializerMethodField(
        help_text=_("Number of related facts")
    )
    
    class Meta:
        model = EvidenceInsight
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "priority_display",
            "tags_list",
            "related_facts",
            "related_facts_count",
            "organization",
            "organization_name",
            "project",
            "project_name",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_name",
            "priority_display",
            "related_facts_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        return list(obj.get_tag_names())
    
    def get_related_facts_count(self, obj):
        """Get count of related facts."""
        return obj.related_facts.count()


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
            "project_name",
            "priority_display",
            "related_facts_count",
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
    
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
        help_text=_("Name of the project"),
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
    
    tags = serializers.SerializerMethodField(
        help_text=_("Tags associated with this recommendation")
    )
    
    related_insights_count = serializers.SerializerMethodField(
        help_text=_("Number of related insights")
    )
    
    class Meta:
        model = Recommendation
        fields = [
            "id",
            "title",
            "description",
            "effort",
            "effort_display",
            "impact",
            "impact_display",
            "tags_list",
            "related_insights",
            "related_insights_count",
            "organization",
            "organization_name",
            "project",
            "project_name",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "project_name",
            "effort_display",
            "impact_display",
            "related_insights_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_tags(self, obj):
        """Get list of tag names for this object."""
        return list(obj.get_tag_names())
    
    def get_related_insights_count(self, obj):
        """Get count of related insights."""
        return obj.related_insights.count()


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
            "project_name",
            "effort_display",
            "impact_display",
            "related_insights_count",
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