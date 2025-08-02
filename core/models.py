import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured


class BaseModel(models.Model):
    """
    Abstract base model that provides UUID primary key, timestamps, 
    soft delete functionality, and audit trail fields.
    
    All models should inherit from this to ensure consistency across the application.
    """
    
    # Define PII fields as a class attribute instead of Meta attribute
    pii_fields = []
    
    class Meta:
        abstract = True
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for this record")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when this record was created")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when this record was last updated")
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp when this record was soft deleted")
    )
    
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        help_text=_("User who created this record")
    )
    
    updated_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        help_text=_("User who last updated this record")
    )
    
    # Organization field will be added later when Organization model is implemented
    # organization = models.ForeignKey(
    #     'core.Organization',
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     help_text=_("Organization this record belongs to")
    # )
    
    def soft_delete(self):
        """Mark this record as deleted without removing it from the database."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
    
    @property
    def is_deleted(self):
        """Check if this record has been soft deleted."""
        return self.deleted_at is not None
    
    def __str__(self):
        """Default string representation using the model name and ID."""
        return f"{self.__class__.__name__} ({str(self.id)[:8]}...)"


class UserManager(BaseUserManager):
    """Custom manager for the User model."""
    
    def create_user(self, email, full_name, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not full_name:
            raise ValueError(_('The Full Name field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, full_name, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom user model that uses email as the username field.
    
    This model includes all the required fields for authentication,
    permissions, and audit tracking.
    """
    
    # Define PII fields as a class attribute
    pii_fields = ['email', 'full_name', 'last_login_ip']
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
    
    email = models.EmailField(
        unique=True,
        help_text=_("Email address used for authentication")
    )
    
    full_name = models.CharField(
        max_length=150,
        help_text=_("Full name of the user")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this user should be treated as active")
    )
    
    is_staff = models.BooleanField(
        default=False,
        help_text=_("Designates whether the user can log into the admin site")
    )
    
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text=_("Date when the user joined")
    )
    
    language = models.CharField(
        max_length=10,
        default='en',
        blank=True,
        help_text=_("Preferred language code")
    )
    
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        blank=True,
        help_text=_("User's timezone")
    )
    
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address of the user's last login")
    )
    
    # Organization field will be added later when Organization model is implemented
    # organization = models.ForeignKey(
    #     'core.Organization',
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     help_text=_("Organization this user belongs to")
    # )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    def get_full_name(self):
        """Return the full name of the user."""
        return self.full_name
    
    def get_short_name(self):
        """Return a short name for the user."""
        return self.full_name.split()[0] if self.full_name else self.email
    
    def __str__(self):
        """Return string representation of the user."""
        return self.email
