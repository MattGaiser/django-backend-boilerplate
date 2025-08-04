import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from faker import Faker

from constants.roles import OrgRole
from core.constants import LanguageChoices, PlanChoices
from core.models import (
    Organization, 
    OrganizationMembership, 
    Project, 
    Tag, 
    User,
    EvidenceSource,
    EvidenceFact,
    EvidenceChunk,
    EvidenceInsight,
    Recommendation,
)

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
    language = LanguageChoices.ENGLISH
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

    title = factory.Faker("catch_phrase")
    description = factory.Faker("text", max_nb_chars=500)
    status = factory.Iterator([choice[0] for choice in Project.StatusChoices.choices])
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
                "status": Project.StatusChoices.IN_PROGRESS,
            }
        )
        return cls(**kwargs)

    @classmethod
    def create_completed_project(cls, **kwargs):
        """Create a completed project."""
        kwargs.update(
            {
                "status": Project.StatusChoices.COMPLETED,
            }
        )
        return cls(**kwargs)


class TagFactory(DjangoModelFactory):
    """Factory for creating Tag instances for testing."""

    class Meta:
        model = Tag

    title = factory.Faker("word")
    definition = factory.Faker("sentence", nb_words=8)
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(UserFactory)


class EvidenceSourceFactory(DjangoModelFactory):
    """Factory for creating EvidenceSource instances for testing."""

    class Meta:
        model = EvidenceSource

    title = factory.Faker("sentence", nb_words=4)
    notes = factory.Faker("text", max_nb_chars=200)
    type = factory.Iterator([choice[0] for choice in EvidenceSource.TypeChoices.choices])
    organization = factory.SubFactory(OrganizationFactory)
    file_path = factory.Faker("file_path")
    file_size = factory.Faker("random_int", min=1024, max=10485760)  # 1KB to 10MB
    mime_type = factory.Faker("mime_type")
    processing_status = EvidenceSource.ProcessingStatusChoices.COMPLETED
    summary = factory.Faker("text", max_nb_chars=500)

    @factory.post_generation
    def add_projects(self, create, extracted, **kwargs):
        """Add projects to the evidence source."""
        if not create:
            return
        
        if extracted:
            for project in extracted:
                self.projects.add(project)
        else:
            # Add a default project
            project = ProjectFactory(organization=self.organization)
            self.projects.add(project)

    @factory.post_generation
    def add_tags(self, create, extracted, **kwargs):
        """Add tags to the created instance."""
        if not create:
            return
        
        if extracted:
            for tag_name in extracted:
                self.add_tag(tag_name, self.organization, self.created_by)


class EvidenceFactFactory(DjangoModelFactory):
    """Factory for creating EvidenceFact instances for testing."""

    class Meta:
        model = EvidenceFact

    title = factory.Faker("sentence", nb_words=6)
    notes = factory.Faker("text", max_nb_chars=300)
    organization = factory.SubFactory(OrganizationFactory)
    source = factory.SubFactory(EvidenceSourceFactory)
    confidence_score = factory.Faker("pyfloat", left_digits=0, right_digits=2, positive=True, min_value=0, max_value=1)
    participant = factory.Faker("name")
    sentiment = factory.Iterator([choice[0] for choice in EvidenceFact.SentimentChoices.choices])
    embedding = factory.LazyFunction(lambda: str([fake.pyfloat() for _ in range(10)]))

    @factory.post_generation
    def add_projects(self, create, extracted, **kwargs):
        """Add projects to the evidence fact."""
        if not create:
            return
        
        if extracted:
            for project in extracted:
                self.projects.add(project)
        else:
            # Add projects from the source
            for project in self.source.projects.all():
                self.projects.add(project)

    @factory.post_generation
    def add_tags(self, create, extracted, **kwargs):
        """Add tags to the created instance."""
        if not create:
            return
        
        if extracted:
            for tag_name in extracted:
                self.add_tag(tag_name, self.organization, self.created_by)


class EvidenceChunkFactory(DjangoModelFactory):
    """Factory for creating EvidenceChunk instances for testing."""

    class Meta:
        model = EvidenceChunk

    organization = factory.SubFactory(OrganizationFactory)
    source = factory.SubFactory(EvidenceSourceFactory)
    chunk_index = factory.Sequence(lambda n: n)
    chunk_text = factory.Faker("text", max_nb_chars=1000)
    embedding = factory.LazyFunction(lambda: str([fake.pyfloat() for _ in range(10)]))
    metadata = factory.Dict({"chunk_size": factory.Faker("random_int", min=100, max=1000)})

    @factory.post_generation
    def add_projects(self, create, extracted, **kwargs):
        """Add projects to the evidence chunk."""
        if not create:
            return
        
        if extracted:
            for project in extracted:
                self.projects.add(project)
        else:
            # Add projects from the source
            for project in self.source.projects.all():
                self.projects.add(project)


class EvidenceInsightFactory(DjangoModelFactory):
    """Factory for creating EvidenceInsight instances for testing."""

    class Meta:
        model = EvidenceInsight

    title = factory.Faker("sentence", nb_words=5)
    notes = factory.Faker("text", max_nb_chars=400)
    organization = factory.SubFactory(OrganizationFactory)
    priority = factory.Iterator([choice[0] for choice in EvidenceInsight.PriorityChoices.choices])
    evidence_score = factory.Faker("random_int", min=1, max=10)
    sentiment = factory.Iterator([choice[0] for choice in EvidenceInsight.SentimentChoices.choices])

    @factory.post_generation
    def add_projects(self, create, extracted, **kwargs):
        """Add projects to the evidence insight."""
        if not create:
            return
        
        if extracted:
            for project in extracted:
                self.projects.add(project)
        else:
            # Add a default project
            project = ProjectFactory(organization=self.organization)
            self.projects.add(project)

    @factory.post_generation
    def add_supporting_evidence(self, create, extracted, **kwargs):
        """Add supporting evidence to the insight."""
        if not create:
            return
        
        if extracted:
            for fact in extracted:
                self.supporting_evidence.add(fact)
        else:
            # Add some default facts
            for _ in range(2):
                fact = EvidenceFactFactory(organization=self.organization)
                self.supporting_evidence.add(fact)

    @factory.post_generation
    def add_tags(self, create, extracted, **kwargs):
        """Add tags to the created instance."""
        if not create:
            return
        
        if extracted:
            for tag_name in extracted:
                self.add_tag(tag_name, self.organization, self.created_by)


class RecommendationFactory(DjangoModelFactory):
    """Factory for creating Recommendation instances for testing."""

    class Meta:
        model = Recommendation

    title = factory.Faker("sentence", nb_words=4)
    notes = factory.Faker("text", max_nb_chars=400)
    organization = factory.SubFactory(OrganizationFactory)
    effort = factory.Iterator([choice[0] for choice in Recommendation.EffortChoices.choices])
    impact = factory.Iterator([choice[0] for choice in Recommendation.ImpactChoices.choices])
    type = factory.Iterator([choice[0] for choice in Recommendation.TypeChoices.choices])
    status = factory.Iterator([choice[0] for choice in Recommendation.StatusChoices.choices])
    evidence_score = factory.Faker("random_int", min=1, max=15)

    @factory.post_generation
    def add_projects(self, create, extracted, **kwargs):
        """Add projects to the recommendation."""
        if not create:
            return
        
        if extracted:
            for project in extracted:
                self.projects.add(project)
        else:
            # Add a default project
            project = ProjectFactory(organization=self.organization)
            self.projects.add(project)

    @factory.post_generation
    def add_supporting_evidence(self, create, extracted, **kwargs):
        """Add supporting evidence to the recommendation."""
        if not create:
            return
        
        if extracted:
            for insight in extracted:
                self.supporting_evidence.add(insight)
        else:
            # Add some default insights
            for _ in range(2):
                insight = EvidenceInsightFactory(organization=self.organization)
                self.supporting_evidence.add(insight)

    @factory.post_generation
    def add_tags(self, create, extracted, **kwargs):
        """Add tags to the created instance."""
        if not create:
            return
        
        if extracted:
            for tag_name in extracted:
                self.add_tag(tag_name, self.organization, self.created_by)
