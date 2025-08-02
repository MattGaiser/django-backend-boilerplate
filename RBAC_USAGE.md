# RBAC (Role-Based Access Control) Usage Guide

This document explains how to use the role-based access control system implemented in this Django boilerplate.

## Overview

The RBAC system provides:
- **Role definitions** in `constants/roles.py`
- **User role checking** via the `has_role()` method
- **View-level protection** via `OrgScopedPermissionMixin`

## Available Roles

Three roles are available in `constants.roles.OrgRole`:

- `ADMIN`: Full administrative access
- `MANAGER`: Management-level access
- `VIEWER`: Read-only access

## Checking User Roles

Use the `has_role()` method on User instances:

```python
from constants.roles import OrgRole

# Check if user has admin role in an organization
if user.has_role(organization, OrgRole.ADMIN):
    # User is an admin in this organization
    print("User has admin access")

# Check for multiple organizations
org1 = Organization.objects.get(name="Company A")
org2 = Organization.objects.get(name="Company B")

admin_in_org1 = user.has_role(org1, OrgRole.ADMIN)
manager_in_org2 = user.has_role(org2, OrgRole.MANAGER)
```

## Protecting Views with Role-Based Access Control

Use `OrgScopedPermissionMixin` to protect class-based views:

### Basic Usage

```python
from django.views.generic import ListView
from core.mixins import OrgScopedPermissionMixin
from constants.roles import OrgRole

class AdminOnlyView(OrgScopedPermissionMixin, ListView):
    required_role = OrgRole.ADMIN
    template_name = 'admin_dashboard.html'
    
    def get_queryset(self):
        # self.organization is available here
        return SomeModel.objects.filter(organization=self.organization)
```

### Multiple Acceptable Roles

```python
class ManagementView(OrgScopedPermissionMixin, ListView):
    required_role = [OrgRole.ADMIN, OrgRole.MANAGER]
    template_name = 'management_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.organization
        return context
```

### Custom Organization Lookup

```python
class CustomLookupView(OrgScopedPermissionMixin, ListView):
    required_role = OrgRole.VIEWER
    org_lookup_field = 'organization_id'  # Default is 'org_id'
    
    # URL pattern would be: /reports/<uuid:organization_id>/
```

### Custom Error Handling

```python
class CustomErrorView(OrgScopedPermissionMixin, ListView):
    required_role = OrgRole.ADMIN
    raise_404_on_no_org = False  # Raise PermissionDenied instead of Http404
```

## URL Patterns

Your URL patterns should include the organization ID:

```python
from django.urls import path
from .views import AdminOnlyView, ManagementView

urlpatterns = [
    path('org/<uuid:org_id>/admin/', AdminOnlyView.as_view(), name='admin-view'),
    path('org/<uuid:org_id>/management/', ManagementView.as_view(), name='management-view'),
]
```

## Creating Organization Memberships

Use the provided factories for testing:

```python
from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole

# Create test data
user = UserFactory()
org = OrganizationFactory()

# Create membership with specific role
admin_membership = OrganizationMembershipFactory(
    user=user,
    organization=org,
    role=OrgRole.ADMIN
)

# Or use convenience methods
admin_membership = OrganizationMembershipFactory.create_admin_membership(
    user=user,
    organization=org
)

manager_membership = OrganizationMembershipFactory.create_manager_membership(
    user=user,
    organization=org
)
```

## Error Responses

The mixin will return appropriate HTTP status codes:

- **403 Forbidden**: User lacks required role or is not a member
- **404 Not Found**: Organization doesn't exist
- **302 Redirect**: User is not authenticated (redirects to login)

## Example: Complete View Implementation

```python
from django.views.generic import CreateView
from django.urls import reverse_lazy
from core.mixins import OrgScopedPermissionMixin
from constants.roles import OrgRole
from .models import Project
from .forms import ProjectForm

class CreateProjectView(OrgScopedPermissionMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'
    required_role = [OrgRole.ADMIN, OrgRole.MANAGER]
    
    def form_valid(self, form):
        # Automatically set the organization
        form.instance.organization = self.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('project-list', kwargs={'org_id': self.organization.id})
```

This provides a complete, secure foundation for implementing organization-scoped, role-based access control in your Django application.