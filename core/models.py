import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured, ValidationError
from constants.roles import OrgRole


class SoftDeleteManager(models.Manager):
    """
    Manager that excludes soft deleted records by default.
    
    This manager provides a default queryset that filters out
    records where deleted_at is not null.
    """
    
    def get_queryset(self):
        """Return queryset excluding soft deleted records."""
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def all_with_deleted(self):
        """Return all records including soft deleted ones."""
        return super().get_queryset()
    
    def deleted_only(self):
        """Return only soft deleted records."""
        return super().get_queryset().filter(deleted_at__isnull=False)


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
    
    # Managers
    objects = SoftDeleteManager()  # Default manager excludes soft deleted records
    all_objects = models.Manager()  # Manager that includes all records
    
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


class Organization(BaseModel):
    """
    Organization model for multi-tenant support.
    
    Represents an organization that users can belong to with different roles.
    """
    
    # Define PII fields as a class attribute
    pii_fields = []
    
    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
    
    name = models.CharField(
        max_length=255,
        help_text=_("Name of the organization")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of the organization")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this organization is active")
    )
    
    language = models.CharField(
        max_length=10,
        default='en',
        blank=True,
        help_text=_("Default language for the organization")
    )
    
    def __str__(self):
        """Return string representation of the organization."""
        return self.name


class UserManager(BaseUserManager):
    """Custom manager for the User model that includes soft delete functionality."""
    
    def get_queryset(self):
        """Return queryset excluding soft deleted records."""
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def all_with_deleted(self):
        """Return all records including soft deleted ones."""
        return super().get_queryset()
    
    def deleted_only(self):
        """Return only soft deleted records."""
        return super().get_queryset().filter(deleted_at__isnull=False)
    
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
    
    # Many-to-many relationship with Organization through OrganizationMembership
    organizations = models.ManyToManyField(
        'core.Organization',
        through='core.OrganizationMembership',
        through_fields=('user', 'organization'),
        related_name='members',
        blank=True,
        help_text=_("Organizations this user belongs to")
    )
    
    objects = UserManager()
    all_objects = models.Manager()  # Manager that includes all records
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    def get_full_name(self):
        """Return the full name of the user."""
        return self.full_name
    
    def get_short_name(self):
        """Return a short name for the user."""
        return self.full_name.split()[0] if self.full_name else self.email
    
    def get_membership(self, organization):
        """
        Get the OrganizationMembership for this user in the specified organization.
        
        Args:
            organization: Organization instance or ID
            
        Returns:
            OrganizationMembership instance or None if not found
        """
        try:
            return self.organization_memberships.get(organization=organization)
        except OrganizationMembership.DoesNotExist:
            return None
    
    def get_role(self, organization):
        """
        Get the role of this user in the specified organization.
        
        Args:
            organization: Organization instance or ID
            
        Returns:
            Role string (from OrgRole.choices) or None if not a member
        """
        membership = self.get_membership(organization)
        return membership.role if membership else None
    
    def get_default_organization(self):
        """
        Get the default organization for this user.
        
        Returns:
            Organization instance or None if no default is set
        """
        try:
            membership = self.organization_memberships.get(is_default=True)
            return membership.organization
        except OrganizationMembership.DoesNotExist:
            return None
    
    def has_role(self, org, role):
        """
        Check if this user has the specified role in the given organization.
        
        Args:
            org: Organization instance or ID
            role: Role string (from OrgRole.choices)
            
        Returns:
            bool: True if user has the role in the organization, False otherwise
        """
        user_role = self.get_role(org)
        return user_role == role
    
    def get_effective_language(self):
        """
        Get the effective language for this user.
        
        Returns:
            str: User's preferred language if set, otherwise organization's default language,
                 or 'en' if no organization default is available.
        """
        if self.language:
            return self.language
        
        # Get default organization's language
        default_org = self.get_default_organization()
        if default_org and default_org.language:
            return default_org.language
        
        return 'en'  # Fallback to English

    def __str__(self):
        """Return string representation of the user."""
        return self.email


class OrganizationMembership(BaseModel):
    """
    Through model for User-Organization many-to-many relationship.
    
    Defines the role and settings for a user's membership in an organization.
    """
    
    # Define PII fields as a class attribute
    pii_fields = []
    
    class Meta:
        verbose_name = _("Organization Membership")
        verbose_name_plural = _("Organization Memberships")
        unique_together = [['user', 'organization']]
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['organization', 'role']),
        ]
    
    user = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        help_text=_("User who is a member of the organization")
    )
    
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='user_memberships',
        help_text=_("Organization the user belongs to")
    )
    
    role = models.CharField(
        max_length=20,
        choices=OrgRole.choices,
        default=OrgRole.VIEWER,
        help_text=_("Role of the user in the organization")
    )
    
    is_default = models.BooleanField(
        default=False,
        help_text=_("Whether this is the user's default organization")
    )
    
    def clean(self):
        """Validate that only one membership per user can be default."""
        super().clean()
        
        if self.is_default and self.user_id:
            # Check if another membership for this user is already default
            existing_default = OrganizationMembership.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk)
            
            if existing_default.exists():
                raise ValidationError({
                    'is_default': _('User can only have one default organization.')
                })
    
    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        """Return string representation of the membership."""
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"


class Project(BaseModel):
    """
    Sample model that inherits from BaseModel for demonstration purposes.
    
    Represents a project within an organization that can have multiple collaborators.
    This model demonstrates the factory pattern and BaseModel inheritance.
    """
    
    # Define PII fields as a class attribute
    pii_fields = []
    
    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['status']),
        ]
    
    class StatusChoices(models.TextChoices):
        """Enumeration of project status options."""
        PLANNING = 'planning', _('Planning')
        ACTIVE = 'active', _('Active')
        ON_HOLD = 'on_hold', _('On Hold')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    name = models.CharField(
        max_length=255,
        help_text=_("Name of the project")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Detailed description of the project")
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNING,
        help_text=_("Current status of the project")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this project is active")
    )
    
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='projects',
        help_text=_("Organization this project belongs to")
    )
    
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Project start date")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Project end date")
    )
    
    def clean(self):
        """Validate that end_date is after start_date."""
        super().clean()
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': _('End date must be after start date.')
            })
    
    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        """Return string representation of the project."""
        return f"{self.name} ({self.organization.name})"
