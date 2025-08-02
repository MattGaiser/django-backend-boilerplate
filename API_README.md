# Django REST Framework API Documentation

This document describes the Django REST Framework API implementation with RBAC, multi-tenancy, versioning, and secure defaults.

## Overview

The API is implemented with the following features:
- Token-based authentication
- Role-based access control (RBAC) with organization scoping
- API versioning (v1) using URL path versioning
- Secure defaults (authentication required, JSON-only responses in production)
- Comprehensive error handling and validation
- PII field tagging and translation support

## Base URL

```
/api/v1/
```

## Authentication

### Token Authentication

All endpoints (except authentication endpoints) require authentication using tokens.

**Obtain Token:**
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "key": "token_string",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "full_name": "User Name",
        "language": "en",
        "timezone": "UTC",
        "date_joined": "2023-01-01T00:00:00Z",
        "is_active": true,
        "organizations": [...],
        "default_organization": {...}
    },
    "created": "2023-01-01T00:00:00Z"
}
```

**Using Token:**
```http
Authorization: Token your_token_here
```

### Other Authentication Endpoints

- `POST /api/v1/auth/revoke-token/` - Revoke current token
- `POST /api/v1/auth/refresh-token/` - Refresh current token
- `GET /api/v1/auth/token-info/` - Get current token info

## User Endpoints

### Current User Profile

**Get Profile:**
```http
GET /api/v1/users/me/
Authorization: Token your_token_here
```

**Update Profile:**
```http
PATCH /api/v1/users/me/
Authorization: Token your_token_here
Content-Type: application/json

{
    "full_name": "New Name",
    "language": "es",
    "timezone": "America/New_York"
}
```

**Change Password:**
```http
POST /api/v1/users/change-password/
Authorization: Token your_token_here
Content-Type: application/json

{
    "current_password": "oldpass",
    "new_password": "newpass123",
    "new_password_confirm": "newpass123"
}
```

### User Management (Admin Only)

**List Users in Organization:**
```http
GET /api/v1/users/
Authorization: Token admin_token_here
```

**Get User Details:**
```http
GET /api/v1/users/{user_id}/
Authorization: Token admin_token_here
```

### Public User Information

**List Organization Members:**
```http
GET /api/v1/public/users/
Authorization: Token your_token_here
```

## API Versioning

### URL Path Versioning (Default)

```http
GET /api/v1/users/me/
```

### Accept Header Versioning

```http
GET /api/v1/users/me/
Accept: application/json; version=1.0
```

Supported version formats:
- `version=1.0`
- `version=v1`
- `version=1`

## Role-Based Access Control

### Organization Roles

- **Admin**: Full access to organization resources and user management
- **Manager**: Access to most organization resources
- **Viewer**: Read-only access to organization resources

### Permission Classes

The API uses custom permission classes:

- `IsAuthenticatedAndInOrgWithRole` - Base permission requiring specific roles
- `IsOrgAdmin` - Requires admin role in organization
- `IsOrgAdminOrManager` - Requires admin or manager role
- `IsOrgMember` - Requires any organization membership
- `IsOwnerOrAdmin` - Allows resource owners or organization admins
- `CanViewUserData` - Allows viewing user data within organization context

### Example Usage in Views

```python
class MyViewSet(BaseViewSet):
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER]
    
    def get_organization(self):
        return self.request.user.get_default_organization()
```

## Error Handling

All errors follow a consistent format:

```json
{
    "error": true,
    "message": "Human-readable error message",
    "details": {
        "field_name": ["Field-specific error"],
        "non_field_errors": ["General errors"]
    },
    "status_code": 400
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation errors)

## Pagination

All list endpoints use page-based pagination:

```json
{
    "count": 100,
    "next": "http://api.example.com/v1/users/?page=3",
    "previous": "http://api.example.com/v1/users/?page=1",
    "results": [...]
}
```

Default page size: 100 items per page.

## Security Features

### Secure Defaults

- Authentication required for all endpoints (except auth)
- JSON-only responses in production (no browsable API)
- Token-based authentication (stateless)
- CSRF protection disabled for API endpoints
- Comprehensive input validation

### Organization Scoping

All resources are automatically scoped to the user's organizations:
- Users can only see resources from organizations they belong to
- Admins can manage users within their organizations
- Cross-organization access is prevented

### PII Handling

User model includes PII fields tracking:
- `email` (PII)
- `full_name` (PII) 
- `last_login_ip` (PII)

These fields are marked in the model's `pii_fields` attribute for compliance tracking.

## Translation Support

All user-facing strings use Django's translation framework:
- Error messages are translatable
- Field help text supports translation
- User can set their preferred language

## Development and Testing

### Running Tests

```bash
# Run all API tests
pytest api/v1/tests/ -v

# Run specific test module
pytest api/v1/tests/test_auth.py -v

# Run all tests including core models
pytest -v
```

### Development Server

```bash
python manage.py runserver
```

API will be available at `http://localhost:8000/api/v1/`

### Creating Test Data

```python
from core.models import User, Organization, OrganizationMembership
from constants.roles import OrgRole

# Create organization
org = Organization.objects.create(name="Test Org")

# Create user
user = User.objects.create_user(
    email="test@example.com",
    full_name="Test User",
    password="testpass123"
)

# Create membership
OrganizationMembership.objects.create(
    user=user,
    organization=org,
    role=OrgRole.ADMIN,
    is_default=True
)
```

## Production Configuration

### Environment Variables

```bash
DEBUG=False
DJANGO_ENV=production
```

### Settings for Production

In production, the API automatically:
- Disables browsable API renderer
- Uses JSON-only responses
- Enables comprehensive logging
- Enforces HTTPS (when properly configured)

### Throttling (Scaffolded)

Throttling classes are configured but disabled by default:
- Anonymous users: No limit (disabled)
- Authenticated users: No limit (disabled)

To enable throttling, update the `DEFAULT_THROTTLE_RATES` in settings:

```python
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',
    'user': '1000/hour',
}
```