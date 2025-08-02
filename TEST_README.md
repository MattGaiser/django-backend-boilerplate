# Test Suite Documentation

This document describes the comprehensive test suite for the Django Backend Boilerplate, focusing on signals, soft deletes, and RBAC functionality.

## Setup

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Running Tests

#### Using Django Test Runner (Recommended)
```bash
python manage.py test core.tests --settings=DjangoBoilerplate.settings
```

#### Using Pytest
```bash
DJANGO_SETTINGS_MODULE=DjangoBoilerplate.settings python -m pytest core/tests/ -v
```

#### Running Specific Test Modules
```bash
# Signal and soft delete tests
python manage.py test core.tests.test_audit_and_soft_delete --settings=DjangoBoilerplate.settings

# RBAC tests
python manage.py test core.tests.test_rbac --settings=DjangoBoilerplate.settings
```

## Test Coverage

### Signal-Based Audit Tests (`test_audit_and_soft_delete.py`)

Tests automatic population of audit fields (`created_by`, `updated_by`) based on thread-local user context:

- **Signal Integration**: Validates that signals properly populate audit fields when user context is available
- **Soft Delete Behavior**: Tests that `soft_delete()` sets `deleted_at` and preserves records in database
- **Thread-Local Context**: Tests proper isolation and cleanup of user context between operations
- **Database Preservation**: Validates that soft-deleted records remain in database vs hard deletes

### RBAC Tests (`test_rbac.py`)

Tests role-based access control with organization membership:

- **Role Hierarchy**: Validates viewer < editor < admin < super_admin permission levels
- **Example Views**: Demonstrates proper RBAC implementation with working view classes
- **Multi-Organization Support**: Tests users with different roles across multiple organizations
- **Permission Enforcement**: Validates that insufficient roles are properly denied access
- **Edge Cases**: Tests authentication requirements, missing organizations, etc.

## Key Testing Patterns

### Using Thread-Local Context

```python
from conftest import ThreadLocalTestMixin

class MyTest(TestCase, ThreadLocalTestMixin):
    def test_audit_fields(self):
        # Create audit user without context to avoid circular references
        self.clear_user_context()
        audit_user = UserFactory()
        
        # Set context for audit tracking
        self.set_user_context(audit_user)
        obj = OrganizationFactory()  # created_by/updated_by automatically set
        
        self.assertEqual(obj.created_by, audit_user)
```

### RBAC Testing

```python
def test_role_access(self):
    request = self.factory.get('/test/')
    request.user = self.viewer_user
    request.test_organization = self.organization
    
    view = ExampleOrganizationView()
    response = view.get(request)
    
    self.assertEqual(response.status_code, 200)
```

### Factory Usage

All tests use `factory_boy` factories for consistent test data:

```python
# Creates user with unique email and proper defaults
user = UserFactory()

# Create organization membership with specific role
membership = OrganizationMembershipFactory(
    user=user,
    organization=organization,
    role=OrgRole.ADMIN
)
```

## Test Isolation

- **Thread-Local Cleanup**: Each test properly cleans up thread-local user context
- **Factory Isolation**: Each factory creates unique, non-conflicting test data
- **Database Transactions**: Django's TestCase provides automatic transaction rollback

## Configuration Files

- **pytest.ini**: Configures pytest with Django settings and test discovery
- **conftest.py**: Provides pytest fixtures and thread-local helpers
- **requirements-dev.txt**: Development and testing dependencies

## Example View Implementation

The test suite includes example view classes demonstrating proper RBAC patterns:

```python
class ExampleOrganizationView(OrganizationRequiredMixin, View):
    required_role = OrgRole.VIEWER  # Minimum required role
    
    def get(self, request):
        organization = self.get_organization(request)
        self.check_organization_access(request, organization)
        return JsonResponse({'message': 'Access granted'})
```

These examples can be used as templates for implementing RBAC in your own views.