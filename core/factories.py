import factory
from factory.django import DjangoModelFactory
from faker import Faker
from core.models import User

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