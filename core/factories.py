import factory
from factory.django import DjangoModelFactory
from faker import Faker
from core.models import User, Organization, OrganizationMembership, OrgRole

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances for testing."""
    
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker('name')
    is_active = True
    is_staff = False
    is_superuser = False
    language = 'en'
    timezone = 'UTC'
    last_login_ip = factory.Faker('ipv4')
    
    @classmethod
    def create_superuser(cls, **kwargs):
        """Create a superuser instance."""
        kwargs.update({
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        })
        return cls(**kwargs)
    
    @classmethod
    def create_staff_user(cls, **kwargs):
        """Create a staff user instance."""
        kwargs.update({
            'is_staff': True,
            'is_active': True,
        })
        return cls(**kwargs)


class OrganizationFactory(DjangoModelFactory):
    """Factory for creating Organization instances for testing."""
    
    class Meta:
        model = Organization
    
    name = factory.Faker('company')
    description = factory.Faker('text', max_nb_chars=200)
    is_active = True


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
        kwargs.update({'is_default': True})
        return cls(**kwargs)
    
    @classmethod
    def create_admin_membership(cls, **kwargs):
        """Create an admin membership."""
        kwargs.update({'role': OrgRole.ADMIN})
        return cls(**kwargs)
    
    @classmethod
    def create_super_admin_membership(cls, **kwargs):
        """Create a super admin membership."""
        kwargs.update({'role': OrgRole.SUPER_ADMIN})
        return cls(**kwargs)