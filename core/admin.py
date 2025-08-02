from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Organization, OrganizationMembership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    
    list_display = ('email', 'full_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'language', 'timezone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Audit'), {'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')}),
        (_('Technical'), {'fields': ('last_login_ip',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'date_joined')
    
    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.append('id')
        return readonly_fields


class OrganizationMembershipInline(admin.TabularInline):
    """Inline admin for organization memberships."""
    model = OrganizationMembership
    extra = 0
    fields = ('user', 'role', 'is_default', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for the Organization model."""
    
    list_display = ('name', 'is_active', 'created_at', 'member_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'is_active')}),
        (_('Audit'), {'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [OrganizationMembershipInline]
    
    def member_count(self, obj):
        """Display the number of members in the organization."""
        return obj.user_memberships.count()
    member_count.short_description = _('Members')
    
    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.append('id')
        return readonly_fields


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for the OrganizationMembership model."""
    
    list_display = ('user', 'organization', 'role', 'is_default', 'created_at')
    list_filter = ('role', 'is_default', 'created_at', 'organization')
    search_fields = ('user__email', 'user__full_name', 'organization__name')
    ordering = ('organization', 'user')
    
    fieldsets = (
        (None, {'fields': ('user', 'organization', 'role', 'is_default')}),
        (_('Audit'), {'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    def get_readonly_fields(self, request, obj=None):
        """Make ID field readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.append('id')
        return readonly_fields
