from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import (
    Organization, 
    OrganizationMembership, 
    Tag, 
    User, 
    Project,
    EvidenceSource,
    EvidenceFact,
    EvidenceChunk,
    EvidenceInsight,
    Recommendation,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = (
        "email",
        "full_name",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_experimental_user_override",
        "date_joined",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_experimental_user_override",
        "date_joined",
    )
    search_fields = ("email", "full_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("full_name", "language", "timezone")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Feature Flags"),
            {
                "fields": ("is_experimental_user_override",),
                "description": _(
                    "Experimental user override only works for superusers"
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
        (_("Technical"), {"fields": ("last_login_ip",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2"),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "date_joined",
    )

    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.append("id")
        return readonly_fields


class OrganizationMembershipInline(admin.TabularInline):
    """Inline admin for organization memberships."""

    model = OrganizationMembership
    extra = 0
    fields = ("user", "role", "is_default", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for the Organization model."""

    list_display = (
        "name",
        "is_active",
        "is_experimental",
        "created_at",
        "member_count",
    )
    list_filter = ("is_active", "is_experimental", "created_at", "plan")
    search_fields = ("name", "description")
    ordering = ("name",)

    fieldsets = (
        (None, {"fields": ("name", "description", "is_active", "language", "plan")}),
        (_("Feature Flags"), {"fields": ("is_experimental",)}),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    inlines = [OrganizationMembershipInline]

    def member_count(self, obj):
        """Display the number of members in the organization."""
        return obj.user_memberships.count()

    member_count.short_description = _("Members")

    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.append("id")
        return readonly_fields


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for the OrganizationMembership model."""

    list_display = ("user", "organization", "role", "is_default", "created_at")
    list_filter = ("role", "is_default", "created_at", "organization")
    search_fields = ("user__email", "user__full_name", "organization__name")
    ordering = ("organization", "user")

    fieldsets = (
        (None, {"fields": ("user", "organization", "role", "is_default")}),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.append("id")
        return readonly_fields


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for the Tag model."""

    list_display = (
        "title",
        "definition_short",
        "organization",
        "usage_count_display",
        "created_at",
        "created_by",
    )
    list_filter = ("organization", "created_at")
    search_fields = ("title", "definition", "organization__name")
    ordering = ("organization", "title")

    fieldsets = (
        (None, {
            "fields": ("title", "definition", "organization"),
            "description": _("Global tag properties. Tags are shared across all data types within the organization.")
        }),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    def definition_short(self, obj):
        """Display a shortened version of the definition."""
        if obj.definition:
            return obj.definition[:50] + "..." if len(obj.definition) > 50 else obj.definition
        return _("No definition")

    definition_short.short_description = _("Definition")

    def usage_count_display(self, obj):
        """Display how many times this tag is used across all models."""
        # Count usage across all taggable models
        usage_count = (
            obj.projects.count() +
            obj.evidence_sources.count() +
            obj.evidence_facts.count() +
            obj.evidence_insights.count() +
            obj.recommendations.count()
        )
        return usage_count

    usage_count_display.short_description = _("Usage Count")

    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.extend(["id", "content_type", "object_id"])
        return readonly_fields


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin configuration for the Project model."""

    list_display = [
        "title",
        "organization",
        "status", 
        "start_date",
        "end_date",
        "created_at",
        "created_by",
    ]
    list_filter = [
        "status",
        "organization",
        "created_at",
    ]
    search_fields = [
        "title",
        "description",
        "organization__name",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
    ]
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("title", "description", "organization")
        }),
        (_("Dates"), {
            "fields": ("start_date", "end_date", "status")
        }),
        (_("Audit Trail"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(EvidenceSource)
class EvidenceSourceAdmin(admin.ModelAdmin):
    """Admin configuration for the EvidenceSource model."""

    list_display = [
        "title",
        "organization",
        "type",
        "processing_status", 
        "created_at",
        "created_by",
    ]
    list_filter = [
        "type",
        "processing_status",
        "organization",
        "created_at",
    ]
    search_fields = [
        "title",
        "notes",
        "organization__name",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
    ]
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("title", "notes", "organization", "type")
        }),
        (_("File Information"), {
            "fields": ("file_path", "file_size", "mime_type", "processing_status")
        }),
        (_("AI Processing"), {
            "fields": ("summary", "metadata")
        }),
        (_("Audit Trail"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )
    filter_horizontal = ["projects"]


@admin.register(EvidenceFact)
class EvidenceFactAdmin(admin.ModelAdmin):
    """Admin configuration for the EvidenceFact model."""

    list_display = [
        "title",
        "organization",
        "source",
        "confidence_score",
        "sentiment", 
        "created_at",
        "created_by",
    ]
    list_filter = [
        "sentiment",
        "organization",
        "created_at",
    ]
    search_fields = [
        "title",
        "notes",
        "participant",
        "organization__name",
        "source__title",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
    ]
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("title", "notes", "organization", "source")
        }),
        (_("Analysis"), {
            "fields": ("confidence_score", "participant", "sentiment")
        }),
        (_("Technical"), {
            "fields": ("embedding", "tags_list")
        }),
        (_("Audit Trail"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )
    filter_horizontal = ["projects"]


@admin.register(EvidenceChunk)
class EvidenceChunkAdmin(admin.ModelAdmin):
    """Admin configuration for the EvidenceChunk model."""

    list_display = [
        "chunk_index",
        "source",
        "organization",
        "created_at",
        "created_by",
    ]
    list_filter = [
        "organization",
        "created_at",
    ]
    search_fields = [
        "chunk_text",
        "organization__name",
        "source__title",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
    ]
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("chunk_index", "chunk_text", "organization", "source")
        }),
        (_("Technical"), {
            "fields": ("embedding", "metadata")
        }),
        (_("Audit Trail"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )
    filter_horizontal = ["projects"]


@admin.register(EvidenceInsight)
class EvidenceInsightAdmin(admin.ModelAdmin):
    """Admin configuration for the EvidenceInsight model."""

    list_display = [
        "title",
        "organization",
        "priority",
        "evidence_score",
        "sentiment",
        "created_at",
        "created_by",
    ]
    list_filter = [
        "priority",
        "sentiment",
        "organization",
        "created_at",
    ]
    search_fields = [
        "title",
        "notes",
        "organization__name",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
        "evidence_level",
    ]
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("title", "notes", "organization", "priority")
        }),
        (_("Evidence"), {
            "fields": ("evidence_score", "evidence_level", "sentiment")
        }),
        (_("Technical"), {
            "fields": ("tags_list",)
        }),
        (_("Audit Trail"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )
    filter_horizontal = ["projects", "supporting_evidence"]


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """Admin configuration for the Recommendation model."""

    list_display = [
        "title",
        "organization",
        "type",
        "status",
        "effort",
        "impact",
        "evidence_score",
        "created_at",
        "created_by",
    ]
    list_filter = [
        "type",
        "status",
        "effort",
        "impact",
        "organization",
        "created_at",
    ]
    search_fields = [
        "title",
        "notes",
        "organization__name",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "deleted_at",
        "evidence_level",
    ]
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("title", "notes", "organization", "type", "status")
        }),
        (_("Impact Assessment"), {
            "fields": ("effort", "impact", "evidence_score", "evidence_level")
        }),
        (_("Technical"), {
            "fields": ("tags_list",)
        }),
        (_("Audit Trail"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )
    filter_horizontal = ["projects", "supporting_evidence"]
