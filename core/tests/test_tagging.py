"""
Tests for the tagging system functionality.

This module tests the Tag model, TaggableMixin, and related functionality
including adding/removing tags, retrieving tags for objects, and filtering
objects by tag names using the new M2M relationship approach.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models

from core.factories import OrganizationFactory, ProjectFactory, TagFactory, UserFactory
from core.models import Project, Tag


@pytest.mark.django_db
class TestTagModel:
    """Test cases for the Tag model."""

    def test_tag_creation(self):
        """Test basic tag creation."""
        org = OrganizationFactory()
        
        tag = TagFactory(title="urgent", organization=org)

        assert tag.title == "urgent"
        assert tag.organization == org
        assert str(tag) == f"urgent ({org.name})"

    def test_tag_str_representation(self):
        """Test tag string representation."""
        tag = TagFactory(title="important")
        expected = f"important ({tag.organization.name})"
        assert str(tag) == expected

    def test_tag_title_validation_empty(self):
        """Test that empty tag titles are not allowed."""
        org = OrganizationFactory()

        tag = Tag(
            title="",
            organization=org,
        )

        with pytest.raises(ValidationError):
            tag.clean()

    def test_tag_title_validation_whitespace_only(self):
        """Test that whitespace-only tag titles are not allowed."""
        tag = TagFactory.build(title="   ")

        with pytest.raises(ValidationError):
            tag.clean()

    def test_tag_title_strips_whitespace(self):
        """Test that tag titles automatically strip whitespace."""
        org = OrganizationFactory()
        
        tag = TagFactory(title="  spaced  ", organization=org)

        assert tag.title == "spaced"

    def test_unique_constraint(self):
        """Test that tag titles must be unique within an organization."""
        org = OrganizationFactory()
        TagFactory(title="duplicate", organization=org)

        # Try to create another tag with the same title in the same org
        with pytest.raises(IntegrityError):
            TagFactory(title="duplicate", organization=org)

    def test_same_tag_different_objects(self):
        """Test that the same tag can be used on different objects."""
        org = OrganizationFactory()
        tag = TagFactory(title="common", organization=org)
        
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)
        
        # Add the same tag to both projects
        project1.tags.add(tag)
        project2.tags.add(tag)
        
        assert tag in project1.tags.all()
        assert tag in project2.tags.all()

    def test_same_tag_different_organizations(self):
        """Test that tags with the same title can exist in different organizations."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()

        tag1 = TagFactory(title="same-title", organization=org1)
        tag2 = TagFactory(title="same-title", organization=org2)

        # Should not raise any exceptions
        assert tag1.title == tag2.title
        assert tag1.organization != tag2.organization

@pytest.mark.django_db
class TestTaggableMixin:
    """Test cases for the TaggableMixin functionality."""

    def test_add_tag_basic(self):
        """Test basic tag addition to an object."""
        project = ProjectFactory()

        tag = project.add_tag("urgent")

        assert tag.title == "urgent"
        assert tag.organization == project.organization
        assert tag in project.tags.all()

    def test_add_tag_with_created_by(self):
        """Test adding a tag with created_by user."""
        project = ProjectFactory()
        user = UserFactory()

        tag = project.add_tag("urgent", created_by=user)

        assert tag.created_by == user

    def test_add_tag_strips_whitespace(self):
        """Test that add_tag strips whitespace from tag titles."""
        project = ProjectFactory()

        tag = project.add_tag("  spaced  ")

        assert tag.title == "spaced"

    def test_add_tag_idempotent(self):
        """Test that adding the same tag twice returns the existing tag."""
        project = ProjectFactory()

        tag1 = project.add_tag("urgent")
        tag2 = project.add_tag("urgent")

        assert tag1 == tag2
        assert project.tags.count() == 1

    def test_add_tag_with_explicit_organization(self):
        """Test adding tag with explicitly provided organization."""
        project = ProjectFactory()
        other_org = OrganizationFactory()
        user = UserFactory()

        tag = project.add_tag("test", organization=other_org, created_by=user)

        assert tag.organization == other_org
        assert tag in project.tags.all()

    def test_remove_tag_existing(self):
        """Test removing an existing tag."""
        project = ProjectFactory()
        tag = project.add_tag("urgent")

        assert tag in project.tags.all()

        result = project.remove_tag("urgent")

        assert result is True
        assert tag not in project.tags.all()

    def test_remove_tag_nonexistent(self):
        """Test removing a non-existent tag returns False."""
        project = ProjectFactory()

        result = project.remove_tag("nonexistent")

        assert result is False

    def test_get_tag_names(self):
        """Test getting all tag names for an object."""
        project = ProjectFactory()
        project.add_tag("urgent")
        project.add_tag("important")

        tag_names = list(project.get_tag_names())

        assert "urgent" in tag_names
        assert "important" in tag_names
        assert len(tag_names) == 2

    def test_has_tag_existing(self):
        """Test checking if object has an existing tag."""
        project = ProjectFactory()
        project.add_tag("urgent")

        assert project.has_tag("urgent")

    def test_has_tag_nonexistent(self):
        """Test checking if object has a non-existent tag."""
        project = ProjectFactory()

        assert not project.has_tag("nonexistent")

    def test_has_tag_different_organization(self):
        """Test that has_tag is organization-scoped."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        project1 = ProjectFactory(organization=org1)
        project2 = ProjectFactory(organization=org2)
        
        # Add tag to project1
        project1.add_tag("urgent")
        
        # Create tag with same title in different org
        project2.add_tag("urgent")
        
        # Both should have the tag in their respective organizations
        assert project1.has_tag("urgent")
        assert project2.has_tag("urgent")


@pytest.mark.django_db  
class TestTaggingQueries:
    """Test cases for querying objects by tags."""

    def test_filter_objects_by_tag_title(self):
        """Test filtering objects by tag title."""
        org = OrganizationFactory()
        tag = TagFactory(title="urgent", organization=org)
        
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)
        project3 = ProjectFactory(organization=org)
        
        # Add tag to projects 1 and 2
        project1.tags.add(tag)
        project2.tags.add(tag)

        # Query projects with the tag
        tagged_projects = Project.objects.filter(tags__title="urgent")

        assert project1 in tagged_projects
        assert project2 in tagged_projects
        assert project3 not in tagged_projects

    def test_filter_by_multiple_tags(self):
        """Test filtering objects by multiple tags."""
        org = OrganizationFactory()
        urgent_tag = TagFactory(title="urgent", organization=org)
        important_tag = TagFactory(title="important", organization=org)
        
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)
        
        # Add both tags to project1, only urgent to project2
        project1.tags.add(urgent_tag, important_tag)
        project2.tags.add(urgent_tag)

        # Query projects with both tags
        projects_with_both = Project.objects.filter(
            tags__title__in=["urgent", "important"]
        ).distinct().annotate(
            tag_count=models.Count('tags')
        ).filter(tag_count=2)

        assert project1 in projects_with_both
        assert project2 not in projects_with_both

    def test_get_all_tags_for_organization(self):
        """Test getting all tags for an organization."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        # Create tags for org1
        tag1 = TagFactory(title="urgent", organization=org1)
        tag2 = TagFactory(title="important", organization=org1)
        
        # Create tag for org2
        TagFactory(title="other", organization=org2)

        org1_tags = Tag.objects.filter(organization=org1)

        assert tag1 in org1_tags
        assert tag2 in org1_tags
        assert len(org1_tags) == 2

    def test_tag_counts_by_title(self):
        """Test getting tag usage counts."""
        org = OrganizationFactory()
        tag = TagFactory(title="popular", organization=org)
        
        # Create projects and add the tag
        for _ in range(3):
            project = ProjectFactory(organization=org)
            project.tags.add(tag)

        # Count usage across projects
        from django.db import models
        tag_usage = Tag.objects.filter(
            organization=org
        ).annotate(
            usage_count=models.Count('projects')
        ).get(title="popular")

        assert tag_usage.usage_count == 3


@pytest.mark.django_db
class TestTagsGlobalFunctionality:
    """Test cases for global tag functionality across different models."""

    def test_tag_shared_across_models(self):
        """Test that tags can be shared across different model types."""
        org = OrganizationFactory()
        tag = TagFactory(title="global", organization=org)
        
        project = ProjectFactory(organization=org)
        
        # Add the same tag to different types of objects
        project.tags.add(tag)
        
        assert tag in project.tags.all()

    def test_tag_cascade_deletion(self):
        """Test that tags are deleted when organization is deleted."""
        org = OrganizationFactory()
        tag = TagFactory(title="test", organization=org)
        
        tag_id = tag.id
        
        # Delete organization
        org.delete()
        
        # Tag should be deleted too
        assert not Tag.objects.filter(id=tag_id).exists()


@pytest.mark.django_db
class TestTagFactory:
    """Test cases for TagFactory."""

    def test_tag_factory_basic(self):
        """Test basic TagFactory functionality."""
        tag = TagFactory()

        assert tag.title is not None
        assert tag.organization is not None
        assert tag.created_by is not None
        assert tag.definition is not None

        result = project.remove_tag("nonexistent")

        assert result is False

    def test_remove_tag_strips_whitespace(self):
        """Test that remove_tag strips whitespace from tag names."""
        project = ProjectFactory()
        project.add_tag("spaced")

        result = project.remove_tag("  spaced  ")

        assert result is True
        assert project.tags.count() == 0

    def test_get_tag_names(self):
        """Test retrieving all tag names for an object."""
        project = ProjectFactory()
        project.add_tag("urgent")
        project.add_tag("important")
        project.add_tag("bug")

        tag_names = list(project.get_tag_names())

        assert len(tag_names) == 3
        assert "urgent" in tag_names
        assert "important" in tag_names
        assert "bug" in tag_names

    def test_get_tag_names_empty(self):
        """Test get_tag_names returns empty list when no tags."""
        project = ProjectFactory()

        tag_names = list(project.get_tag_names())

        assert tag_names == []

    def test_has_tag_existing(self):
        """Test has_tag returns True for existing tags."""
        project = ProjectFactory()
        project.add_tag("urgent")

        assert project.has_tag("urgent") is True

    def test_has_tag_nonexistent(self):
        """Test has_tag returns False for non-existent tags."""
        project = ProjectFactory()

        assert project.has_tag("nonexistent") is False

    def test_has_tag_strips_whitespace(self):
        """Test that has_tag strips whitespace from tag names."""
        project = ProjectFactory()
        project.add_tag("spaced")

        assert project.has_tag("  spaced  ") is True


@pytest.mark.django_db
class TestTaggingQueries:
    """Test cases for querying and filtering tagged objects."""

    def test_filter_objects_by_tag_name(self):
        """Test filtering objects by tag name."""
        org = OrganizationFactory()
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)
        project3 = ProjectFactory(organization=org)

        project1.add_tag("urgent")
        project2.add_tag("urgent")
        project3.add_tag("normal")

        # Filter projects with "urgent" tag
        urgent_projects = Project.objects.filter(
            tags__name="urgent", tags__organization=org
        ).distinct()

        assert project1 in urgent_projects
        assert project2 in urgent_projects
        assert project3 not in urgent_projects
        assert urgent_projects.count() == 2

    def test_filter_by_multiple_tags(self):
        """Test filtering objects that have multiple specific tags."""
        org = OrganizationFactory()
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)

        project1.add_tag("urgent")
        project1.add_tag("bug")
        project2.add_tag("urgent")
        project2.add_tag("feature")

        # Find projects that are both urgent and bug
        urgent_bug_projects = (
            Project.objects.filter(tags__name="urgent", tags__organization=org)
            .filter(tags__name="bug", tags__organization=org)
            .distinct()
        )

        assert project1 in urgent_bug_projects
        assert project2 not in urgent_bug_projects
        assert urgent_bug_projects.count() == 1

    def test_get_all_tags_for_organization(self):
        """Test retrieving all tags for an organization."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()

        project1 = ProjectFactory(organization=org1)
        project2 = ProjectFactory(organization=org2)

        project1.add_tag("tag1")
        project1.add_tag("tag2")
        project2.add_tag("tag3")

        org1_tags = Tag.objects.filter(organization=org1)
        org2_tags = Tag.objects.filter(organization=org2)

        assert org1_tags.count() == 2
        assert org2_tags.count() == 1

        org1_tag_names = set(org1_tags.values_list("name", flat=True))
        assert org1_tag_names == {"tag1", "tag2"}

    def test_get_tagged_objects_by_content_type(self):
        """Test retrieving all objects of a specific type that have tags."""
        org = OrganizationFactory()
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)
        project3 = ProjectFactory(organization=org)

        project1.add_tag("test")
        project2.add_tag("demo")
        # project3 has no tags

        project_content_type = ContentType.objects.get_for_model(Project)
        tagged_projects = Project.objects.filter(
            id__in=Tag.objects.filter(
                content_type=project_content_type, organization=org
            ).values_list("object_id", flat=True)
        )

        assert project1 in tagged_projects
        assert project2 in tagged_projects
        assert project3 not in tagged_projects
        assert tagged_projects.count() == 2

    def test_tag_counts_by_name(self):
        """Test counting how many objects have each tag."""
        org = OrganizationFactory()
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)
        project3 = ProjectFactory(organization=org)

        project1.add_tag("urgent")
        project2.add_tag("urgent")
        project3.add_tag("normal")

        from django.db.models import Count

        tag_counts = (
            Tag.objects.filter(organization=org)
            .values("name")
            .annotate(count=Count("id"))
            .order_by("name")
        )

        tag_counts_dict = {item["name"]: item["count"] for item in tag_counts}

        assert tag_counts_dict["urgent"] == 2
        assert tag_counts_dict["normal"] == 1


@pytest.mark.django_db
class TestTagsGenericForeignKey:
    """Test cases for generic foreign key functionality."""

    def test_tag_different_model_types(self):
        """Test tagging different types of models."""
        org = OrganizationFactory()
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)

        # Tag different projects to test generic foreign key works with same model type
        project1_tag = project1.add_tag("project1-tag")
        project2_tag = project2.add_tag("project2-tag")

        assert project1_tag.content_type == ContentType.objects.get_for_model(Project)
        assert project2_tag.content_type == ContentType.objects.get_for_model(Project)

        assert project1_tag.content_object == project1
        assert project2_tag.content_object == project2

        # Test that each project has its own tags
        assert project1.has_tag("project1-tag")
        assert not project1.has_tag("project2-tag")
        assert project2.has_tag("project2-tag")
        assert not project2.has_tag("project1-tag")

    def test_content_object_deletion_cascades(self):
        """Test that tags are deleted when the tagged object is deleted."""
        project = ProjectFactory()
        project.add_tag("test-tag")

        tag_count_before = Tag.objects.count()
        assert tag_count_before == 1

        project.delete()

        tag_count_after = Tag.objects.count()
        assert tag_count_after == 0

    def test_organization_deletion_cascades(self):
        """Test that tags are deleted when the organization is deleted."""
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)
        project.add_tag("test-tag")

        tag_count_before = Tag.objects.count()
        assert tag_count_before == 1

        org.delete()

        tag_count_after = Tag.objects.count()
        assert tag_count_after == 0


@pytest.mark.django_db
class TestTagFactory:
    """Test cases for the TagFactory."""

    def test_tag_factory_basic(self):
        """Test basic TagFactory functionality."""
        tag = TagFactory()

        assert tag.name
        assert tag.organization
        assert tag.content_object
        assert tag.content_type
        assert tag.object_id

    def test_tag_factory_for_object(self):
        """Test TagFactory.create_for_object method."""
        project = ProjectFactory()

        tag = TagFactory.create_for_object(content_object=project, name="custom-tag")

        assert tag.name == "custom-tag"
        assert tag.content_object == project
        assert tag.organization == project.organization
        assert tag.content_type == ContentType.objects.get_for_model(Project)
        assert tag.object_id == project.id
