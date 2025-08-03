from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Organization, OrganizationMembership, Tag, User


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
        "name",
        "organization",
        "content_type",
        "content_object_display",
        "created_at",
        "created_by",
    )
    list_filter = ("organization", "content_type", "created_at")
    search_fields = ("name", "organization__name")
    ordering = ("organization", "name")

    fieldsets = (
        (None, {"fields": ("name", "organization")}),
        (
            _("Tagged Object"),
            {"fields": ("content_type", "object_id", "content_object_display")},
        ),
        (
            _("Audit"),
            {"fields": ("created_by", "updated_by", "created_at", "updated_at")},
        ),
    )

    readonly_fields = (
        "content_object_display",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    def content_object_display(self, obj):
        """Display the tagged object in a readable format."""
        if obj.content_object:
            return str(obj.content_object)
        return _("Object not found")

    content_object_display.short_description = _("Tagged Object")

    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.extend(["id", "content_type", "object_id"])
        return readonly_fields
