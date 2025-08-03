# 🧠 Copilot Instructions for Django Development

This document defines the standards, architecture, and coding practices Copilot must follow when assisting with Django development. The goals are long-term maintainability, auditability, extensibility, and enterprise readiness from the start.

---

## ✅ Foundational Goals

- All models must support audit logging, soft delete, PII tracking, and multi-tenancy.
- All data access must respect role-based access control (RBAC) and organizational scope.
- The project must be ready for internationalization (i18n), API versioning, structured logging, and test automation from the outset.
- All testing must use Pytest and factories, with third-party integrations handled via VCR.py.
- Code must be modular, documented, and production-ready.

---

## 🏗️ Models and Database Design

### `BaseModel`
- All models must inherit from a common abstract `BaseModel`:
  - `id = UUIDField(primary_key=True)`
  - `created_at`, `updated_at` (timestamped)
  - `deleted_at` for soft delete
  - `created_by`, `updated_by` (linked via signal to current user)
  - `organization = ForeignKey(Organization)`
  - All fields must include `verbose_name` and `help_text`
  - Required: `Meta.pii_fields = [...]` for any model that includes PII

### Soft Delete
- Implemented via a nullable `deleted_at` field.
- Soft-deleted objects must be excluded from default querysets.
- Provide `.all_objects` and `.active_objects` managers.

### Slugs and URLs
- Models exposed via URL (e.g., Organization) must have a `slug` field.
- Implement `get_absolute_url()` for any model used in routes or links.

---

## 🔐 RBAC and Organizational Scope

### Organization & Membership
- Users are connected to organizations via a through model `OrganizationMembership`.
- Membership includes a `role` (ADMIN, MANAGER, VIEWER) using a shared enum.
- Users may belong to multiple orgs, with one marked as `is_default`.

### Permissions
- All data access must be scoped to the user's role in the organization.
- Views must use a DRF permission class like:
  ```python
  class IsAuthenticatedAndInOrgWithRole:
      ...
  ```

- `User.get_role(org)` and `User.has_role(org, role)` helpers must be implemented.

---

## 🌐 Django REST Framework

- Use `rest_framework` with:
  - `IsAuthenticated` as default permission
  - `PageNumberPagination`
  - JSON-only rendering (no BrowsableAPIRenderer in prod)
  - URLPathVersioning (e.g., `/api/v1/`)
- All API endpoints must validate org membership and RBAC.
- Use viewsets and serializers organized under `api/v1/`

---

## 🌍 Internationalization (i18n)

- All strings must be wrapped in `gettext_lazy`.
- Provide `LANGUAGE_CODE = 'en'` and scaffolding for `'fr'`.
- Add translation for all model field labels and enums.

---

## 📚 Constants and Enums

- Create a shared `constants.py` or `enums.py`:
  - Use `TextChoices` for enums: `OrgRole`, `Plan`, `Language`, etc.
  - All choices must use `gettext_lazy` for i18n compatibility.

---

## 🧪 Testing and Developer Experience

- All tests must be written in **Pytest**.
- Use `factory_boy` for test data.
- Use `pytest-django` for model tests and API tests.
- Use `VCR.py` for all tests involving external APIs — no mocks for HTTP requests.
- Include fixtures for demo data (e.g., org, user, tags).
- Provide a one-command dev setup with Docker.

---

## 📦 Tagging System

- Tags should be implemented using `GenericForeignKey` and `GenericRelation`.
- Models that support tagging must inherit from `TaggableMixin`.

---

## 📈 Logging and Observability

- Use `structlog` or `python-json-logger` for structured logging.
- Include `request_id`, `user_id`, `org_id` in all log entries.
- Provide middleware to generate and attach `request_id` to thread-local storage.
- Ensure logs are JSON-formatted and compatible with centralized log aggregators.

---

## 🔄 Versioning and Change Tracking

- Expose version info via `/version.json`:
  - `commit`, `timestamp`, `branch`
- Generate `version.json` at build time via script
- Maintain a `CHANGELOG.md` using [Keep a Changelog](https://keepachangelog.com) format

---

## 🧠 Additional Guidelines

- Never use raw JSON fields for dynamic config — prefer normalized models.
- Never use default Django User — always use custom `User` model.
- All models, views, and serializers must be documented with docstrings.
- All admin interfaces should include `list_display`, `search_fields`, `readonly_fields`.

---

## 🆕 Adding New Models

When adding new models to the project, follow these steps:

### 1. Model Structure

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, TaggableMixin

class YourModel(BaseModel, TaggableMixin):
    """
    Docstring describing the model's purpose and functionality.
    
    This model represents [description] and supports [features].
    """
    
    # Define PII fields FIRST (required for any model with PII)
    pii_fields = ["name", "email"]  # List any fields containing PII
    
    class Meta:
        verbose_name = _("Your Model")
        verbose_name_plural = _("Your Models")
        indexes = [
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_name_per_org"
            )
        ]
    
    # Organization field (required for multi-tenancy)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="your_models",
        help_text=_("Organization this record belongs to"),
    )
    
    # Required fields with proper help_text and verbose_name
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Name of the item"),
    )
    
    # Optional fields
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed description"),
    )
    
    # Use TextChoices for status fields
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        PENDING = "pending", _("Pending")
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name=_("Status"),
        help_text=_("Current status"),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this item is active"),
    )
    
    def clean(self):
        """Custom validation logic."""
        super().clean()
        # Add custom validation here
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation."""
        return f"{self.name} ({self.organization.name})"
```

### 2. Model Admin

```python
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "organization",
        "status", 
        "is_active",
        "created_at",
        "created_by",
    ]
    list_filter = [
        "status",
        "is_active", 
        "organization",
        "created_at",
    ]
    search_fields = [
        "name",
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
            "fields": ("name", "description", "organization")
        }),
        (_("Status"), {
            "fields": ("status", "is_active")
        }),
        (_("Audit Trail"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )
```

### 3. Model Factory

```python
import factory
from django.utils import timezone
from core.factories import OrganizationFactory, UserFactory
from .models import YourModel

class YourModelFactory(factory.django.DjangoModelFactory):
    """Factory for creating YourModel instances."""
    
    class Meta:
        model = YourModel
    
    name = factory.Sequence(lambda n: f"Item {n}")
    description = factory.Faker("text", max_nb_chars=200)
    organization = factory.SubFactory(OrganizationFactory)
    status = YourModel.StatusChoices.ACTIVE
    is_active = True
    created_by = factory.SubFactory(UserFactory)
    
    @factory.post_generation
    def add_tags(self, create, extracted, **kwargs):
        """Add tags to the created instance."""
        if not create:
            return
        
        if extracted:
            for tag_name in extracted:
                self.add_tag(tag_name, self.organization, self.created_by)
```

### 4. Model Tests

```python
import pytest
from django.core.exceptions import ValidationError
from core.factories import OrganizationFactory, UserFactory
from .factories import YourModelFactory
from .models import YourModel

@pytest.mark.django_db
class TestYourModel:
    def test_create_model(self):
        """Test creating a new model instance."""
        model = YourModelFactory()
        assert model.name
        assert model.organization
        assert model.status == YourModel.StatusChoices.ACTIVE
        assert str(model.id)  # UUID should be set
    
    def test_model_str_representation(self):
        """Test string representation."""
        model = YourModelFactory(name="Test Item")
        expected = f"Test Item ({model.organization.name})"
        assert str(model) == expected
    
    def test_soft_delete(self):
        """Test soft delete functionality."""
        model = YourModelFactory()
        assert not model.is_deleted
        
        model.soft_delete()
        assert model.is_deleted
        assert model.deleted_at
    
    def test_pii_fields_declared(self):
        """Test that PII fields are properly declared."""
        assert hasattr(YourModel, 'pii_fields')
        assert isinstance(YourModel.pii_fields, list)
    
    def test_tagging_functionality(self):
        """Test tagging mixin functionality."""
        model = YourModelFactory()
        
        # Add tag
        tag = model.add_tag("test-tag", model.organization, model.created_by)
        assert tag.name == "test-tag"
        
        # Check tag exists
        assert model.has_tag("test-tag", model.organization)
        
        # Get tag names
        tag_names = list(model.get_tag_names())
        assert "test-tag" in tag_names
        
        # Remove tag
        removed = model.remove_tag("test-tag", model.organization)
        assert removed
        assert not model.has_tag("test-tag", model.organization)
```

---

## 🛣️ Adding New Routes/API Endpoints

When adding new API endpoints, follow these patterns:

### 1. Serializer Structure

```python
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    """
    Serializer for YourModel with proper validation and organization scoping.
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
    
    tags = serializers.SerializerMethodField(
        help_text=_("Tags associated with this item")
    )
    
    class Meta:
        model = YourModel
        fields = [
            "id",
            "name",
            "description",
            "organization",
            "organization_name",
            "status",
            "status_display",
            "is_active",
            "tags",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "organization",  # Set automatically by viewset
            "organization_name",
            "status_display",
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
        
        # Check for uniqueness within organization
        organization = self.context.get('organization')
        if organization:
            existing = YourModel.objects.filter(
                organization=organization,
                name__iexact=value.strip()
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    _("An item with this name already exists in the organization.")
                )
        
        return value.strip()

class CreateYourModelSerializer(YourModelSerializer):
    """Serializer for creating new instances."""
    
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        help_text=_("List of tag names to add to the item"),
    )
    
    class Meta(YourModelSerializer.Meta):
        fields = YourModelSerializer.Meta.fields
        read_only_fields = [
            "id",
            "organization",
            "organization_name", 
            "status_display",
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
```

### 2. ViewSet Structure

```python
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from api.v1.views.base import BaseViewSet, BaseReadOnlyViewSet
from api.v1.serializers.your_model import YourModelSerializer, CreateYourModelSerializer
from constants.roles import OrgRole
from .models import YourModel

class YourModelViewSet(BaseViewSet):
    """
    ViewSet for YourModel management.
    
    Provides CRUD operations with proper organization scoping and RBAC.
    """
    
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    required_roles = [OrgRole.ADMIN, OrgRole.MANAGER]  # Who can manage these resources
    
    def get_queryset(self):
        """Filter queryset by user's organizations."""
        if not self.request.user.is_authenticated:
            return YourModel.objects.none()
        
        # Get organizations where user has required access
        user_org_ids = self.request.user.organization_memberships.filter(
            role__in=self.required_roles
        ).values_list("organization_id", flat=True)
        
        return YourModel.objects.filter(
            organization_id__in=user_org_ids
        ).select_related('organization', 'created_by')
    
    def get_serializer_class(self):
        """Return appropriate serializer for the action."""
        if self.action == 'create':
            return CreateYourModelSerializer
        return YourModelSerializer
    
    def get_serializer_context(self):
        """Add organization to serializer context."""
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context
    
    @action(
        detail=True,
        methods=['post'],
        url_path='add-tag',
        url_name='add-tag'
    )
    def add_tag(self, request, pk=None):
        """
        Add a tag to the item.
        
        POST /api/v1/your-models/{id}/add-tag/
        Body: {"name": "tag-name"}
        """
        instance = self.get_object()
        tag_name = request.data.get('name')
        
        if not tag_name:
            return Response(
                {"error": _("Tag name is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tag = instance.add_tag(
                tag_name,
                instance.organization,
                request.user
            )
            return Response({
                "message": _("Tag added successfully."),
                "tag": {"name": tag.name, "id": str(tag.id)}
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(
        detail=True,
        methods=['delete'],
        url_path='remove-tag',
        url_name='remove-tag'
    )
    def remove_tag(self, request, pk=None):
        """
        Remove a tag from the item.
        
        DELETE /api/v1/your-models/{id}/remove-tag/
        Body: {"name": "tag-name"}
        """
        instance = self.get_object()
        tag_name = request.data.get('name')
        
        if not tag_name:
            return Response(
                {"error": _("Tag name is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        removed = instance.remove_tag(tag_name, instance.organization)
        
        if removed:
            return Response({"message": _("Tag removed successfully.")})
        else:
            return Response(
                {"error": _("Tag not found.")},
                status=status.HTTP_404_NOT_FOUND
            )

class PublicYourModelViewSet(BaseReadOnlyViewSet):
    """
    Public read-only endpoints for YourModel.
    
    Provides limited information accessible to any org member.
    """
    
    queryset = YourModel.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return minimal serializer for public access."""
        from rest_framework import serializers
        
        class PublicYourModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = YourModel
                fields = ["id", "name", "status", "created_at"]
                read_only_fields = ["id", "name", "status", "created_at"]
        
        return PublicYourModelSerializer
    
    def get_queryset(self):
        """Return items from user's organizations."""
        if not self.request.user.is_authenticated:
            return YourModel.objects.none()
        
        user_org_ids = self.request.user.organizations.values_list("id", flat=True)
        
        return YourModel.objects.filter(
            organization_id__in=user_org_ids,
            is_active=True
        ).select_related('organization')
```

### 3. URL Registration

```python
# In api/v1/urls.py

from api.v1.views.your_model import YourModelViewSet, PublicYourModelViewSet

# Add to router registration
router.register(r"your-models", YourModelViewSet, basename="your-models")
router.register(r"public/your-models", PublicYourModelViewSet, basename="public-your-models")
```

### 4. API Tests

```python
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory
from constants.roles import OrgRole
from .factories import YourModelFactory

@pytest.mark.django_db
class TestYourModelAPI:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.org = OrganizationFactory()
        self.admin_user = UserFactory()
        self.viewer_user = UserFactory()
        
        # Create memberships
        OrganizationMembershipFactory(
            user=self.admin_user,
            organization=self.org,
            role=OrgRole.ADMIN,
            is_default=True
        )
        OrganizationMembershipFactory(
            user=self.viewer_user,
            organization=self.org,
            role=OrgRole.VIEWER,
            is_default=True
        )
        
        self.item = YourModelFactory(organization=self.org)
    
    def test_list_items_as_admin(self):
        """Admin can list items."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('your-models-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == self.item.name
    
    def test_list_items_as_viewer_forbidden(self):
        """Viewer cannot list items (admin/manager only)."""
        self.client.force_authenticate(user=self.viewer_user)
        url = reverse('your-models-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_item(self):
        """Admin can create new items."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('your-models-list')
        
        data = {
            'name': 'New Item',
            'description': 'Test description',
            'status': 'active',
            'tags': ['tag1', 'tag2']
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Item'
        assert response.data['organization'] == str(self.org.id)
        assert 'tag1' in response.data['tags']
        assert 'tag2' in response.data['tags']
    
    def test_add_tag_to_item(self):
        """Test adding tag via API endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('your-models-add-tag', kwargs={'pk': self.item.pk})
        
        data = {'name': 'new-tag'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Tag added successfully' in response.data['message']
        
        # Verify tag was added
        self.item.refresh_from_db()
        assert self.item.has_tag('new-tag', self.org)
    
    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests are denied."""
        url = reverse('your-models-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cross_organization_access_denied(self):
        """Users cannot access items from other organizations."""
        other_org = OrganizationFactory()
        other_item = YourModelFactory(organization=other_org)
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('your-models-detail', kwargs={'pk': other_item.pk})
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

### 5. Function-Based Views (Alternative)

For simple endpoints that don't need full CRUD:

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def your_model_stats(request):
    """
    Get statistics for user's organization.
    
    GET /api/v1/your-models/stats/
    """
    organization = request.user.get_default_organization()
    if not organization:
        return Response(
            {"error": _("No default organization found.")},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user has access
    if not request.user.has_role(organization, OrgRole.VIEWER):
        return Response(
            {"error": _("Insufficient permissions.")},
            status=status.HTTP_403_FORBIDDEN
        )
    
    stats = {
        'total_items': YourModel.objects.filter(organization=organization).count(),
        'active_items': YourModel.objects.filter(
            organization=organization,
            is_active=True
        ).count(),
        'by_status': {}
    }
    
    # Get counts by status
    for status_choice in YourModel.StatusChoices:
        count = YourModel.objects.filter(
            organization=organization,
            status=status_choice.value
        ).count()
        stats['by_status'][status_choice.value] = count
    
    return Response(stats)

# Add to urls.py:
# path("your-models/stats/", your_model_stats, name="your-model-stats"),
```

---

## 🔧 Tools to Be Used

| Purpose         | Tool / Library                       |
| --------------- | ------------------------------------ |
| API Framework   | Django REST Framework                |
| Testing         | Pytest, FactoryBoy, VCR.py           |
| Auth            | Custom User + OrganizationMembership |
| i18n            | gettext\_lazy + `makemessages`       |
| Logging         | structlog or python-json-logger      |
| API Versioning  | URLPathVersioning (`/api/v1/`)       |
| Slug Generation | slugify(name)                        |
| Permissions     | Custom DRF permission classes        |

---

## 📦 Future-Proofing (Track Separately)

- Feature flag framework
- Webhook system
- Fine-grained per-resource permissions
- Multi-region deployments
- Export/import support

---

This file should be kept in the project root as `copilot-instructions.md` and updated as architectural decisions evolve.