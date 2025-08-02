# Core Models Documentation

## Custom User Model

This project uses a custom User model (`core.models.User`) instead of Django's default User model. The custom User model provides:

### Features

- **Email-based authentication**: Users log in with their email address instead of a username
- **UUID primary keys**: All users have UUID-based primary keys for better security and scalability
- **Extended user fields**: Additional fields like `language`, `timezone`, and `last_login_ip`
- **Audit trail**: Automatic tracking of created_by, updated_by, created_at, and updated_at
- **Soft delete support**: Users can be soft-deleted instead of permanently removed
- **PII compliance**: Proper declaration of PII fields for compliance tracking

### Usage

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a regular user
user = User.objects.create_user(
    email='user@example.com',
    full_name='John Doe',
    password='secure_password'
)

# Create a superuser
admin = User.objects.create_superuser(
    email='admin@example.com',
    full_name='Admin User',
    password='admin_password'
)
```

## BaseModel Abstract Class

All models in this project should inherit from `BaseModel` to ensure consistency and provide common functionality.

### Features

- **UUID primary keys**: Automatic UUID generation for all records
- **Audit timestamps**: Automatic `created_at` and `updated_at` timestamps
- **User tracking**: Automatic `created_by` and `updated_by` user assignment
- **Soft delete**: Built-in soft delete functionality with `deleted_at` field
- **PII compliance**: Enforced declaration of PII fields for compliance

### Usage

```python
from core.models import BaseModel
from django.db import models

class YourModel(BaseModel):
    # Declare any PII fields for compliance tracking
    pii_fields = ['customer_email', 'customer_name']
    
    name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=150)
    
    class Meta:
        verbose_name = "Your Model"
        verbose_name_plural = "Your Models"

# Usage
instance = YourModel.objects.create(name="Test", customer_email="test@example.com")

# Soft delete
instance.soft_delete()
print(instance.is_deleted)  # True

# Check audit fields
print(instance.created_at)
print(instance.created_by)  # Will be set automatically if user is logged in
```

### PII Compliance

The system automatically validates that models containing PII fields have proper `pii_fields` declarations:

```python
class CompliantModel(BaseModel):
    # These fields contain PII, so they must be declared
    pii_fields = ['email', 'full_name', 'phone_number']
    
    email = models.EmailField()
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    
    # Non-PII fields don't need to be declared
    description = models.TextField()
```

If you forget to declare PII fields, the system will raise an `ImproperlyConfigured` error during model loading.

### Automatic User Assignment

The system automatically tracks which user created or updated records:

```python
# When a logged-in user creates or updates a record,
# created_by and updated_by are automatically set
with current_user_context(request.user):
    instance = YourModel.objects.create(name="Test")
    # instance.created_by will be set to request.user
    
    instance.name = "Updated"
    instance.save()
    # instance.updated_by will be set to request.user
```

This is handled automatically by the `CurrentUserMiddleware` and Django signals.

## Testing

The project includes comprehensive tests and factories for testing:

```python
from core.factories import UserFactory

# Create test users
user = UserFactory()
admin = UserFactory.create_superuser()
staff_user = UserFactory.create_staff_user()

# Use in tests
class YourTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
    
    def test_something(self):
        # Your test code here
        pass
```

## Admin Interface

The custom User model is fully integrated with Django's admin interface, providing:

- Email-based login
- Organized field groups (Personal info, Permissions, Audit, Technical)
- Proper search and filtering
- Read-only audit fields
- PII field help text and internationalization