import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from faker import Faker

from constants.roles import OrgRole
from core.constants import LanguageChoices, PlanChoices
from core.models import Organization, OrganizationMembership, Project, Tag, User

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances for testing."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    is_active = True
    is_staff = False
    is_superuser = False
    language = factory.Iterator([choice[0] for choice in LanguageChoices.choices])
    timezone = "UTC"
    last_login_ip = factory.Faker("ipv4")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password for the user."""
        if not create:
            return

        password = extracted or "testpass123"
        self.set_password(password)
        self.save()

    @classmethod
    def create_superuser(cls, **kwargs):
        """Create a superuser instance."""
        kwargs.update(
            {
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            }
        )
        return cls(**kwargs)

    @classmethod
    def create_staff_user(cls, **kwargs):
        """Create a staff user instance."""
        kwargs.update(
            {
                "is_staff": True,
                "is_active": True,
            }
        )
        return cls(**kwargs)


class OrganizationFactory(DjangoModelFactory):
    """Factory for creating Organization instances for testing."""

    class Meta:
        model = Organization

    name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=200)
    is_active = True
    plan = factory.Iterator([choice[0] for choice in PlanChoices.choices])
    language = factory.Iterator([choice[0] for choice in LanguageChoices.choices])


class OrganizationMembershipFactory(DjangoModelFactory):
    """Factory for creating OrganizationMembership instances for testing."""

    class Meta:
        model = OrganizationMembership

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    role = factory.Iterator([choice[0] for choice in OrgRole.choices])
    is_default = False

    @classmethod
    def create_default_membership(cls, **kwargs):
        """Create a default membership for a user."""
        kwargs.update({"is_default": True})
        return cls(**kwargs)

    @classmethod
    def create_admin_membership(cls, **kwargs):
        """Create an admin membership."""
        kwargs.update({"role": OrgRole.ADMIN})
        return cls(**kwargs)

    @classmethod
    def create_manager_membership(cls, **kwargs):
        """Create a manager membership."""
        kwargs.update({"role": OrgRole.MANAGER})
        return cls(**kwargs)

    @classmethod
    def create_super_admin_membership(cls, **kwargs):
        """Create a super admin membership."""
        kwargs.update({"role": OrgRole.SUPER_ADMIN})
        return cls(**kwargs)


class ProjectFactory(DjangoModelFactory):
    """Factory for creating Project instances for testing."""

    class Meta:
        model = Project

    name = factory.Faker("catch_phrase")
    description = factory.Faker("text", max_nb_chars=500)
    status = factory.Iterator([choice[0] for choice in Project.StatusChoices.choices])
    is_active = True
    organization = factory.SubFactory(OrganizationFactory)
    start_date = factory.Faker("date_this_year")
    end_date = factory.LazyAttribute(
        lambda obj: (
            fake.date_between(start_date=obj.start_date, end_date="+1y")
            if obj.start_date
            else None
        )
    )

    @classmethod
    def create_active_project(cls, **kwargs):
        """Create an active project."""
        kwargs.update(
            {
                "status": Project.StatusChoices.ACTIVE,
                "is_active": True,
            }
        )
        return cls(**kwargs)

    @classmethod
    def create_completed_project(cls, **kwargs):
        """Create a completed project."""
        kwargs.update(
            {
                "status": Project.StatusChoices.COMPLETED,
                "is_active": False,
            }
        )
        return cls(**kwargs)


class TagFactory(DjangoModelFactory):
    """Factory for creating Tag instances for testing."""

    class Meta:
        model = Tag

    name = factory.Faker("word")
    organization = factory.SubFactory(OrganizationFactory)
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(Project)
    )
    object_id = factory.SelfAttribute("content_object.id")
    content_object = factory.SubFactory(
        ProjectFactory, organization=factory.SelfAttribute("..organization")
    )

    @classmethod
    def create_for_object(cls, content_object, **kwargs):
        """Create a tag for a specific object."""
        kwargs.update(
            {
                "content_type": ContentType.objects.get_for_model(content_object),
                "object_id": content_object.id,
                "content_object": content_object,
            }
        )
        if hasattr(content_object, "organization") and "organization" not in kwargs:
            kwargs["organization"] = content_object.organization
        return cls(**kwargs)
