"""
Serializers for tag-related models.

Provides serialization and validation for Tags with proper organization scoping.
Based on the Tags Specification for global tag management.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from core.models import Tag


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for Tag with proper validation and organization scoping.
    
    Follows Tags Specification for global tag management:
    - Title: The tag label
    - Definition (optional): Describes the intended use or scope of the tag
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    class Meta:
        model = Tag
        fields = [
            "id",
            "title",
            "definition",
            "organization",
            "organization_name",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def validate_title(self, value):
        """Validate tag title."""
        if not value or not value.strip():
            raise serializers.ValidationError(_("Tag title cannot be empty."))
        return value.strip()


class CreateTagSerializer(TagSerializer):
    """Serializer for creating new tags."""
    
    class Meta(TagSerializer.Meta):
        fields = TagSerializer.Meta.fields
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "created_at",
            "updated_at",
            "created_by",
        ]


class TagSummarySerializer(serializers.Serializer):
    """
    Serializer for tag summary information (used in tag listing endpoints).
    
    Provides a comprehensive view of tags with usage statistics and metadata.
    """
    
    title = serializers.CharField(
        help_text=_("Title of the tag")
    )
    
    definition = serializers.CharField(
        allow_blank=True,
        help_text=_("Definition of the tag's intended use or scope")
    )
    
    category = serializers.CharField(
        allow_blank=True,
        help_text=_("Category of the tag")
    )
    
    color = serializers.CharField(
        allow_blank=True,
        help_text=_("Color code for the tag")
    )
    
    status = serializers.ChoiceField(
        choices=[
            ("pending", _("Pending")),
            ("approved", _("Approved")),
            ("rejected", _("Rejected")),
        ],
        default="pending",
        help_text=_("Status of the tag")
    )
    
    usage_count = serializers.IntegerField(
        read_only=True,
        help_text=_("Number of times this tag is used")
    )
    
    project_id = serializers.UUIDField(
        help_text=_("Project this tag belongs to")
    )
    
    user_id = serializers.UUIDField(
        read_only=True,
        help_text=_("User who created this tag")
    )
    
    created_at = serializers.DateTimeField(
        read_only=True,
        help_text=_("When this tag was created")
    )
    
    updated_at = serializers.DateTimeField(
        read_only=True,
        help_text=_("When this tag was last updated")
    )


class CreateTagSummarySerializer(TagSummarySerializer):
    """Serializer for creating new tag summaries."""
    
    class Meta:
        fields = [
            "title",
            "definition",
            "category",
            "color",
            "status",
            "project_id",
        ]


class UpdateTagSummarySerializer(serializers.Serializer):
    """Serializer for updating tag summaries."""
    
    title = serializers.CharField(
        required=False,
        help_text=_("Title of the tag")
    )
    
    definition = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Definition of the tag's intended use or scope")
    )
    
    category = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Category of the tag")
    )
    
    color = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Color code for the tag")
    )
    
    status = serializers.ChoiceField(
        choices=[
            ("pending", _("Pending")),
            ("approved", _("Approved")),
            ("rejected", _("Rejected")),
        ],
        required=False,
        help_text=_("Status of the tag")
    )