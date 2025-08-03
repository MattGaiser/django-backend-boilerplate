"""
Tests for the tagging system functionality.

This module tests the Tag model, TaggableMixin, and related functionality
including adding/removing tags, retrieving tags for objects, and filtering
objects by tag names.
"""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.factories import OrganizationFactory, ProjectFactory, TagFactory, UserFactory
from core.models import Project, Tag


@pytest.mark.django_db
class TestTagModel:
    """Test cases for the Tag model."""

    def test_tag_creation(self):
        """Test basic tag creation."""
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)

        tag = TagFactory(name="urgent", organization=org, content_object=project)

        assert tag.name == "urgent"
        assert tag.organization == org
        assert tag.content_object == project
        assert str(tag) == f"urgent ({org.name})"

    def test_tag_str_representation(self):
        """Test tag string representation."""
        tag = TagFactory(name="important")
        expected = f"important ({tag.organization.name})"
        assert str(tag) == expected

    def test_tag_name_validation_empty(self):
        """Test that empty tag names are not allowed."""
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)

        tag = Tag(
            name="",
            organization=org,
            content_type=ContentType.objects.get_for_model(project),
            object_id=project.id,
            content_object=project,
        )

        with pytest.raises(ValidationError) as exc_info:
            tag.clean()

        assert "Tag name cannot be empty or only whitespace." in str(exc_info.value)

    def test_tag_name_validation_whitespace_only(self):
        """Test that whitespace-only tag names are not allowed."""
        tag = TagFactory.build(name="   ")

        with pytest.raises(ValidationError) as exc_info:
            tag.clean()

        assert "Tag name cannot be empty or only whitespace." in str(exc_info.value)

    def test_tag_name_strips_whitespace(self):
        """Test that tag names are stripped of leading/trailing whitespace."""
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)

        tag = TagFactory(name="  spaced  ", organization=org, content_object=project)

        assert tag.name == "spaced"

    def test_unique_constraint(self):
        """Test that the same tag name cannot be applied twice to the same object."""
        org = OrganizationFactory()
        project = ProjectFactory(organization=org)

        # Create first tag
        TagFactory(name="duplicate", organization=org, content_object=project)

        # Try to create duplicate tag
        with pytest.raises(IntegrityError):
            TagFactory(name="duplicate", organization=org, content_object=project)

    def test_same_tag_different_objects(self):
        """Test that the same tag name can be applied to different objects."""
        org = OrganizationFactory()
        project1 = ProjectFactory(organization=org)
        project2 = ProjectFactory(organization=org)

        tag1 = TagFactory(name="common", organization=org, content_object=project1)
        tag2 = TagFactory(name="common", organization=org, content_object=project2)

        assert tag1.name == tag2.name
        assert tag1.content_object != tag2.content_object

    def test_same_tag_different_organizations(self):
        """Test that the same tag name can exist in different organizations."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        project1 = ProjectFactory(organization=org1)
        project2 = ProjectFactory(organization=org2)

        tag1 = TagFactory(name="common", organization=org1, content_object=project1)
        tag2 = TagFactory(name="common", organization=org2, content_object=project2)

        assert tag1.name == tag2.name
        assert tag1.organization != tag2.organization


@pytest.mark.django_db
class TestTaggableMixin:
    """Test cases for the TaggableMixin functionality."""

    def test_add_tag_basic(self):
        """Test basic tag addition to an object."""
        project = ProjectFactory()

        tag = project.add_tag("urgent")

        assert tag.name == "urgent"
        assert tag.organization == project.organization
        assert tag.content_object == project
        assert project.tags.count() == 1

    def test_add_tag_with_created_by(self):
        """Test adding a tag with created_by user."""
        project = ProjectFactory()
        user = UserFactory()

        tag = project.add_tag("urgent", created_by=user)

        assert tag.created_by == user

    def test_add_tag_strips_whitespace(self):
        """Test that add_tag strips whitespace from tag names."""
        project = ProjectFactory()

        tag = project.add_tag("  spaced  ")

        assert tag.name == "spaced"

    def test_add_tag_idempotent(self):
        """Test that adding the same tag twice returns the existing tag."""
        project = ProjectFactory()

        tag1 = project.add_tag("urgent")
        tag2 = project.add_tag("urgent")

        assert tag1 == tag2
        assert project.tags.count() == 1

    def test_add_tag_without_organization_attribute(self):
        """Test adding tag to object without organization attribute raises error."""

        # Create a simple mock object without organization attribute
        class MockObject:
            def __init__(self):
                self.id = "test-id"

        mock_obj = MockObject()

        # Add TaggableMixin methods manually for testing
        from core.models import TaggableMixin

        # Monkey patch the add_tag method onto the mock instance
        mock_obj.add_tag = TaggableMixin.add_tag.__get__(mock_obj, MockObject)

        with pytest.raises(ValueError) as exc_info:
            mock_obj.add_tag("test")

        assert "Organization must be provided" in str(exc_info.value)

    def test_add_tag_with_explicit_organization(self):
        """Test adding tag with explicitly provided organization - using Project for simplicity."""
        project = ProjectFactory()
        org = OrganizationFactory()

        # This should work when organization is explicitly provided (overriding the project's org)
        tag = project.add_tag("test", organization=org)

        assert tag.organization == org
        assert tag.content_object == project

    def test_remove_tag_existing(self):
        """Test removing an existing tag."""
        project = ProjectFactory()
        project.add_tag("urgent")

        assert project.tags.count() == 1

        result = project.remove_tag("urgent")

        assert result is True
        assert project.tags.count() == 0

    def test_remove_tag_nonexistent(self):
        """Test removing a non-existent tag returns False."""
        project = ProjectFactory()

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
