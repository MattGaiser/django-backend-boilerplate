"""
Serializers for organization and project models.

Provides serialization and validation for Organizations, Projects,
and Organization Memberships with proper RBAC.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from core.models import Organization, Project, OrganizationMembership
from constants.roles import OrgRole


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for Organization with proper validation.
    """
    
    plan_display = serializers.CharField(
        source="get_plan_display",
        read_only=True,
        help_text=_("Human-readable plan name"),
    )
    
    language_display = serializers.CharField(
        source="get_language_display",
        read_only=True,
        help_text=_("Human-readable language name"),
    )
    
    members_count = serializers.SerializerMethodField(
        help_text=_("Number of members in the organization")
    )
    
    projects_count = serializers.SerializerMethodField(
        help_text=_("Number of projects in the organization")
    )
    
    user_role = serializers.SerializerMethodField(
        help_text=_("Current user's role in this organization")
    )
    
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "plan",
            "plan_display",
            "language",
            "language_display",
            "is_experimental",
            "members_count",
            "projects_count",
            "user_role",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "plan_display",
            "language_display",
            "members_count",
            "projects_count",
            "user_role",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def get_members_count(self, obj):
        """Get count of organization members."""
        return obj.user_memberships.count()
    
    def get_projects_count(self, obj):
        """Get count of organization projects."""
        return obj.projects.count()
    
    def get_user_role(self, obj):
        """Get current user's role in this organization."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.get_role(obj)
        return None
    
    def validate_name(self, value):
        """Validate name field."""
        if not value or not value.strip():
            raise serializers.ValidationError(_("Name cannot be empty."))
        return value.strip()


class CreateOrganizationSerializer(OrganizationSerializer):
    """Serializer for creating new organizations."""
    
    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields
        read_only_fields = [
            "id",
            "plan_display",
            "language_display",
            "members_count",
            "projects_count",
            "user_role",
            "created_at",
            "updated_at",
            "created_by",
        ]


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project with proper validation and organization scoping.
    """
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
        help_text=_("Human-readable status"),
    )
    
    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "status",
            "status_display",
            "start_date",
            "end_date",
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
            "status_display",
            "created_at",
            "updated_at",
            "created_by",
        ]
    
    def validate_title(self, value):
        """Validate title field."""
        if not value or not value.strip():
            raise serializers.ValidationError(_("Title cannot be empty."))
        
        # Check for uniqueness within organization
        organization = self.context.get('organization')
        if organization:
            existing = Project.objects.filter(
                organization=organization,
                title__iexact=value.strip()
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    _("A project with this title already exists in the organization.")
                )
        
        return value.strip()


class CreateProjectSerializer(serializers.ModelSerializer):
    """Serializer for creating new projects."""
    
    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "status",
            "start_date",
            "end_date",
            "organization",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",
            "created_at",
            "updated_at",
            "created_by",
        ]


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for OrganizationMembership with proper validation.
    """
    
    user_email = serializers.CharField(
        source="user.email",
        read_only=True,
        help_text=_("Email of the user"),
    )
    
    user_full_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
        help_text=_("Full name of the user"),
    )
    
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )
    
    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
        help_text=_("Human-readable role name"),
    )
    
    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "organization",
            "organization_name",
            "role",
            "role_display",
            "is_default",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "user_full_name",
            "organization_name",
            "role_display",
            "created_at",
            "updated_at",
            "created_by",
        ]


class SimplifiedOrganizationSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for Organization for use in nested contexts.
    """
    
    user_role = serializers.SerializerMethodField(
        help_text=_("Current user's role in this organization")
    )
    
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "user_role",
        ]
        read_only_fields = [
            "id",
            "name",
            "description",
            "is_active",
            "user_role",
        ]
    
    def get_user_role(self, obj):
        """Get current user's role in this organization."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.get_role(obj)
        return None


class OrganizationMembershipListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing organizations via memberships (matching Supabase pattern).
    """
    
    organization = SimplifiedOrganizationSerializer(read_only=True)
    
    class Meta:
        model = OrganizationMembership
        fields = [
            "organization",
            "role",
            "is_default",
        ]
        read_only_fields = [
            "organization",
            "role",
            "is_default",
        ]