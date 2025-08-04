import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from constants.roles import OrgRole
from core.constants import LanguageChoices, PlanChoices


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

    # Define PII fields as a class attribute (empty by default for abstract base model)
    pii_fields = []

    class Meta:
        abstract = True

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for this record"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, help_text=_("Timestamp when this record was created")
    )

    updated_at = models.DateTimeField(
        auto_now=True, help_text=_("Timestamp when this record was last updated")
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp when this record was soft deleted"),
    )

    created_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        help_text=_("User who created this record"),
    )

    updated_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        help_text=_("User who last updated this record"),
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
        self.save(update_fields=["deleted_at"])

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
    pii_fields = ["name"]

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    name = models.CharField(max_length=255, help_text=_("Name of the organization"))

    description = models.TextField(
        blank=True, help_text=_("Description of the organization")
    )

    is_active = models.BooleanField(
        default=True, help_text=_("Designates whether this organization is active")
    )

    plan = models.CharField(
        max_length=20,
        choices=PlanChoices.choices,
        default=PlanChoices.FREE,
        help_text=_("Subscription plan for the organization"),
    )

    language = models.CharField(
        max_length=10,
        choices=LanguageChoices.choices,
        default=LanguageChoices.get_default_language(),
        blank=True,
        help_text=_("Default language for the organization"),
    )

    is_experimental = models.BooleanField(
        default=False, help_text=_("Enable experimental features for this organization")
    )

    def __str__(self):
        """Return string representation of the organization."""
        return self.name

    def get_plan_limits(self):
        """
        Get the limits for this organization's plan.

        Returns:
            dict: Dictionary containing limits for the organization's plan
        """
        return PlanChoices.get_plan_limits(self.plan)

    def is_premium_plan(self):
        """
        Check if this organization has a premium plan.

        Returns:
            bool: True if organization has a premium plan, False otherwise
        """
        return PlanChoices.is_premium_plan(self.plan)

    def can_add_users(self, additional_users=1):
        """
        Check if organization can add more users based on plan limits.

        Args:
            additional_users: Number of additional users to check for

        Returns:
            bool: True if organization can add the users, False otherwise
        """
        limits = self.get_plan_limits()
        max_users = limits.get("max_users")

        if max_users is None:  # Unlimited
            return True

        current_users = self.user_memberships.count()
        return (current_users + additional_users) <= max_users


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
            raise ValueError(_("The Email field must be set"))
        if not full_name:
            raise ValueError(_("The Full Name field must be set"))

        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom user model that uses email as the username field.

    This model includes all the required fields for authentication,
    permissions, and audit tracking.
    """

    # Define PII fields as a class attribute
    pii_fields = ["email", "full_name", "last_login_ip"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined", "email"]  # Order by newest first, then by email

    email = models.EmailField(
        unique=True, help_text=_("Email address used for authentication")
    )

    full_name = models.CharField(max_length=150, help_text=_("Full name of the user"))

    is_active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this user should be treated as active"),
    )

    is_staff = models.BooleanField(
        default=False,
        help_text=_("Designates whether the user can log into the admin site"),
    )

    date_joined = models.DateTimeField(
        default=timezone.now, help_text=_("Date when the user joined")
    )

    language = models.CharField(
        max_length=10,
        choices=LanguageChoices.choices,
        default=LanguageChoices.get_default_language(),
        blank=True,
        help_text=_("Preferred language code"),
    )

    timezone = models.CharField(
        max_length=50, default="UTC", blank=True, help_text=_("User's timezone")
    )

    last_login_ip = models.GenericIPAddressField(
        null=True, blank=True, help_text=_("IP address of the user's last login")
    )

    is_experimental_user_override = models.BooleanField(
        default=False,
        help_text=_(
            "Allow superuser to override experimental features (superuser only)"
        ),
    )

    # Many-to-many relationship with Organization through OrganizationMembership
    organizations = models.ManyToManyField(
        "core.Organization",
        through="core.OrganizationMembership",
        through_fields=("user", "organization"),
        related_name="members",
        blank=True,
        help_text=_("Organizations this user belongs to"),
    )

    objects = UserManager()
    all_objects = models.Manager()  # Manager that includes all records

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

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
                 or default language if no organization default is available.
        """
        if self.language:
            return self.language

        # Get default organization's language
        default_org = self.get_default_organization()
        if default_org and default_org.language:
            return default_org.language

        return LanguageChoices.get_default_language()  # Fallback to default language

    def is_experimental_enabled(self):
        """
        Check if experimental features are enabled for this user.

        Returns:
            bool: True if experimental features are enabled, False otherwise
        """
        # Superuser override takes precedence
        if self.is_superuser and self.is_experimental_user_override:
            return True

        # Check default organization's experimental flag
        default_org = self.get_default_organization()
        if default_org:
            return default_org.is_experimental

        # Default to False if no organization
        return False

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
        unique_together = [["user", "organization"]]
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["organization", "role"]),
        ]

    user = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        help_text=_("User who is a member of the organization"),
    )

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="user_memberships",
        help_text=_("Organization the user belongs to"),
    )

    role = models.CharField(
        max_length=20,
        choices=OrgRole.choices,
        default=OrgRole.VIEWER,
        help_text=_("Role of the user in the organization"),
    )

    is_default = models.BooleanField(
        default=False, help_text=_("Whether this is the user's default organization")
    )

    def clean(self):
        """Validate that only one membership per user can be default."""
        super().clean()

        if self.is_default and self.user_id:
            # Check if another membership for this user is already default
            existing_default = OrganizationMembership.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk)

            if existing_default.exists():
                raise ValidationError(
                    {"is_default": _("User can only have one default organization.")}
                )

    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Return string representation of the membership."""
        return (
            f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
        )


class TaggableMixin(models.Model):
    """
    Abstract mixin that adds tagging functionality to any model.

    This mixin provides a ManyToMany relationship to the Tag model and
    helper methods for managing tags on the model instance.
    """

    class Meta:
        abstract = True

    # Note: tags field is added to each concrete model that uses this mixin
    # since we can't have a generic M2M field in an abstract base class

    def add_tag(self, title, organization=None, created_by=None, definition=""):
        """
        Add a tag to this object.

        Args:
            title (str): Title of the tag
            organization: Organization for the tag (uses self.organization if available)
            created_by: User who created the tag
            definition (str): Optional definition for the tag

        Returns:
            Tag: The created or existing tag

        Raises:
            ValueError: If organization cannot be determined
        """
        # Try to get organization from the object itself if not provided
        if organization is None:
            if hasattr(self, "organization"):
                organization = self.organization
            else:
                raise ValueError(
                    _(
                        "Organization must be provided or object must have an organization attribute"
                    )
                )

        # Get or create the tag
        from core.models import Tag

        tag, created = Tag.objects.get_or_create(
            title=title.strip(),
            organization=organization,
            defaults={"created_by": created_by, "definition": definition},
        )
        
        # Add the tag to this object's tags if not already added
        if hasattr(self, 'tags'):
            self.tags.add(tag)
        
        return tag

    def remove_tag(self, title, organization=None):
        """
        Remove a tag from this object.

        Args:
            title (str): Title of the tag to remove
            organization: Organization for the tag (uses self.organization if available)

        Returns:
            bool: True if tag was removed, False if tag didn't exist
        """
        # Try to get organization from the object itself if not provided
        if organization is None:
            if hasattr(self, "organization"):
                organization = self.organization
            else:
                raise ValueError(
                    _(
                        "Organization must be provided or object must have an organization attribute"
                    )
                )

        try:
            from core.models import Tag

            tag = Tag.objects.get(
                title=title.strip(),
                organization=organization,
            )
            # Remove the tag from this object's tags if it exists
            if hasattr(self, 'tags'):
                self.tags.remove(tag)
            return True
        except Tag.DoesNotExist:
            return False

    def get_tag_names(self):
        """
        Get all tag titles for this object.

        Returns:
            QuerySet: QuerySet of tag titles
        """
        if hasattr(self, 'tags'):
            return self.tags.values_list("title", flat=True)
        return []

    def has_tag(self, title, organization=None):
        """
        Check if this object has a specific tag.

        Args:
            title (str): Title of the tag to check
            organization: Organization for the tag (uses self.organization if available)

        Returns:
            bool: True if object has the tag, False otherwise
        """
        # Try to get organization from the object itself if not provided
        if organization is None:
            if hasattr(self, "organization"):
                organization = self.organization
            else:
                raise ValueError(
                    _(
                        "Organization must be provided or object must have an organization attribute"
                    )
                )

        if hasattr(self, 'tags'):
            return self.tags.filter(title=title.strip(), organization=organization).exists()
        return False


class Tag(BaseModel):
    """
    Global tag model for flexible, lightweight categorization of content.

    Tags are scoped by organization and provide a shared tag set across all data types.
    They enable filtering, cross-linking, and reporting without rigid hierarchies.
    
    Features:
    - Tags apply globally across the organization account
    - Same tag set is shared across all data types
    - Tags can be created manually or via AI tooling
    - Tags can be merged manually
    """

    # Define PII fields as a class attribute
    pii_fields = ["title", "definition"]

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        indexes = [
            models.Index(fields=["organization", "title"]),
            models.Index(fields=["organization", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "title"],
                name="unique_tag_title_per_org",
            )
        ]

    title = models.CharField(
        max_length=100, 
        verbose_name=_("Title"),
        help_text=_("The tag label")
    )

    definition = models.TextField(
        blank=True,
        verbose_name=_("Definition"),
        help_text=_("Optional description of the intended use or scope of the tag")
    )

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="tags",
        verbose_name=_("Organization"),
        help_text=_("Organization this tag belongs to"),
    )

    def clean(self):
        """Validate tag data."""
        super().clean()

        # Ensure tag title is not empty after stripping whitespace
        if self.title is not None:
            self.title = self.title.strip()

        if (
            not self.title
        ):  # This catches None, empty string, and whitespace-only strings
            raise ValidationError(
                {"title": _("Tag title cannot be empty or only whitespace.")}
            )

    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Return string representation of the tag."""
        return f"{self.title} ({self.organization.name})"


class Project(BaseModel, TaggableMixin):
    """
    Project model for managing research projects within an organization.

    Represents a project that contains sources, observations, insights, 
    and recommendations for analysis and decision making.
    """

    # Define PII fields as a class attribute
    pii_fields = ["title", "description"]

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        indexes = [
            models.Index(fields=["organization", "title"]),
            models.Index(fields=["status"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    class StatusChoices(models.TextChoices):
        """Enumeration of project status options."""

        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        ON_HOLD = "on_hold", _("On Hold")

    # Organization field (required for multi-tenancy)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="projects",
        help_text=_("Organization this project belongs to"),
    )

    title = models.CharField(
        max_length=255, 
        verbose_name=_("Title"),
        help_text=_("Short text title of the project")
    )

    description = models.TextField(
        blank=True, 
        verbose_name=_("Description"),
        help_text=_("Longer text description (hypothesis or goal)")
    )

    start_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_("Start Date"),
        help_text=_("Project start date")
    )

    end_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_("End Date"),
        help_text=_("Project end date")
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NOT_STARTED,
        verbose_name=_("Status"),
        help_text=_("Current status of the project"),
    )

    # Tags relationship - global repository tags
    tags = models.ManyToManyField(
        "core.Tag",
        blank=True,
        related_name="projects",
        verbose_name=_("Tags"),
        help_text=_("Global repository tags")
    )

    def clean(self):
        """Validate that end_date is after start_date."""
        super().clean()

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({"end_date": _("End date must be after start date.")})

    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Return string representation of the project."""
        return f"{self.title} ({self.organization.name})"


class EvidenceSource(BaseModel, TaggableMixin):
    """
    Evidence source model for storing uploaded files and content.
    
    Represents documents, videos, audio files, images, or text content
    that serve as sources for analysis. Maps to "Sources" in specification.
    """
    
    # Define PII fields as a class attribute
    pii_fields = ["title", "notes"]
    
    class Meta:
        verbose_name = _("Evidence Source")
        verbose_name_plural = _("Evidence Sources")
        indexes = [
            models.Index(fields=["organization", "type"]),
            models.Index(fields=["processing_status"]),
            models.Index(fields=["created_at"]),
        ]
    
    class TypeChoices(models.TextChoices):
        """Enumeration of evidence source types."""
        SUPPORT_TICKETS = "support_tickets", _("Support Tickets")
        INTERVIEW = "interview", _("Interview")
        SURVEY = "survey", _("Survey")
        ANALYTICS = "analytics", _("Analytics")
        DOCUMENT = "document", _("Document")
        VIDEO = "video", _("Video")
        AUDIO = "audio", _("Audio")
        TEXT = "text", _("Text")
        IMAGE = "image", _("Image")
    
    class ProcessingStatusChoices(models.TextChoices):
        """Enumeration of processing status options."""
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")
    
    # Organization field (required for multi-tenancy and RBAC)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="evidence_sources",
        help_text=_("Organization this evidence source belongs to"),
    )
    
    # Project can be multiple - use M2M instead of single FK for flexibility
    projects = models.ManyToManyField(
        "core.Project",
        blank=True,
        related_name="evidence_sources",
        verbose_name=_("Projects"),
        help_text=_("Projects this evidence source belongs to (optional)"),
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Smaller text area, always visible"),
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Detailed description, expandable by user"),
    )
    
    type = models.CharField(
        max_length=20,
        choices=TypeChoices.choices,
        verbose_name=_("Type"),
        help_text=_("Open text (e.g., Support Tickets, Interview, Survey, Analytics)"),
    )
    
    # Technical file-related fields for uploaded content
    file_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("File Path"),
        help_text=_("Path to the uploaded file in storage"),
    )
    
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("File Size"),
        help_text=_("Size of the uploaded file in bytes"),
    )
    
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("MIME Type"),
        help_text=_("MIME type of the uploaded file"),
    )
    
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatusChoices.choices,
        default=ProcessingStatusChoices.PENDING,
        verbose_name=_("Processing Status"),
        help_text=_("Current processing status"),
    )
    
    # Legacy fields for backward compatibility
    summary = models.TextField(
        blank=True,
        verbose_name=_("Summary"),
        help_text=_("AI-generated summary of the content"),
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata including legacy tags"),
    )

    # Tags relationship - global repository tags
    tags = models.ManyToManyField(
        "core.Tag",
        blank=True,
        related_name="evidence_sources",
        verbose_name=_("Tags"),
        help_text=_("Global repository tags")
    )
    
    def __str__(self):
        """Return string representation of the evidence source."""
        return f"{self.title} ({self.organization.name})"


class EvidenceFact(BaseModel, TaggableMixin):
    """
    Evidence fact model for storing extracted facts from evidence sources.
    
    Represents individual facts or insights extracted from evidence sources
    through AI processing or manual input. Maps to "Observations" in specification.
    """
    
    # Define PII fields as a class attribute
    pii_fields = ["title", "notes", "participant"]
    
    class Meta:
        verbose_name = _("Evidence Fact")
        verbose_name_plural = _("Evidence Facts")
        indexes = [
            models.Index(fields=["organization", "source"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["confidence_score"]),
            models.Index(fields=["sentiment"]),
        ]
    
    class SentimentChoices(models.TextChoices):
        """Enumeration of sentiment options."""
        POSITIVE = "positive", _("Positive")
        NEUTRAL = "neutral", _("Neutral")
        NEGATIVE = "negative", _("Negative")
    
    # Organization field (required for multi-tenancy and RBAC)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="evidence_facts",
        help_text=_("Organization this evidence fact belongs to"),
    )
    
    # Projects can be multiple (optional)
    projects = models.ManyToManyField(
        "core.Project",
        blank=True,
        related_name="evidence_facts",
        verbose_name=_("Projects"),
        help_text=_("Projects this observation belongs to (optional, can be multiple)"),
    )
    
    # Source is required (linked to 1 and only 1 source)
    source = models.ForeignKey(
        "core.EvidenceSource",
        on_delete=models.CASCADE,
        related_name="evidence_facts",
        verbose_name=_("Source"),
        help_text=_("Evidence source this fact was extracted from (required)"),
    )
    
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Title"),
        help_text=_("Title or heading for the evidence fact"),
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional context; expandable"),
    )
    
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Confidence Score"),
        help_text=_("AI confidence score for this fact (0.0 to 1.0)"),
    )
    
    participant = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Participant"),
        help_text=_("Participant or speaker associated with this fact (optional)"),
    )
    
    sentiment = models.CharField(
        max_length=20,
        choices=SentimentChoices.choices,
        null=True,
        blank=True,
        verbose_name=_("Sentiment"),
        help_text=_("Sentiment analysis of the fact (optional)"),
    )
    
    # Technical embedding field for AI processing
    embedding = models.TextField(
        blank=True,
        verbose_name=_("Embedding"),
        help_text=_("Vector embedding for similarity search"),
    )
    
    # Legacy field for backward compatibility
    tags_list = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Tags List"),
        help_text=_("Legacy list of tag names for this fact"),
    )

    # Tags relationship - global repository tags
    tags = models.ManyToManyField(
        "core.Tag",
        blank=True,
        related_name="evidence_facts",
        verbose_name=_("Tags"),
        help_text=_("Global repository tags")
    )
    
    def __str__(self):
        """Return string representation of the evidence fact."""
        title = self.title or str(self.id)[:8]
        return f"{title} ({self.source.title})"


class EvidenceChunk(BaseModel):
    """
    Evidence chunk model for storing processed chunks from evidence sources.
    
    Represents smaller pieces of content created during document processing
    for better AI analysis and similarity search.
    """
    
    # Define PII fields as a class attribute
    pii_fields = ["chunk_text"]
    
    class Meta:
        verbose_name = _("Evidence Chunk")
        verbose_name_plural = _("Evidence Chunks")
        indexes = [
            models.Index(fields=["organization", "source"]),
            models.Index(fields=["chunk_index"]),
        ]
    
    # Organization field (required for multi-tenancy and RBAC)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="evidence_chunks",
        help_text=_("Organization this evidence chunk belongs to"),
    )
    
    # Projects can be multiple (inferred from source)
    projects = models.ManyToManyField(
        "core.Project",
        blank=True,
        related_name="evidence_chunks",
        verbose_name=_("Projects"),
        help_text=_("Projects this evidence chunk belongs to (inferred from source)"),
    )
    
    source = models.ForeignKey(
        "core.EvidenceSource",
        on_delete=models.CASCADE,
        related_name="evidence_chunks",
        help_text=_("Evidence source this chunk was created from"),
    )
    
    chunk_index = models.PositiveIntegerField(
        verbose_name=_("Chunk Index"),
        help_text=_("Order index of this chunk within the source"),
    )
    
    chunk_text = models.TextField(
        verbose_name=_("Chunk Text"),
        help_text=_("Text content of this chunk"),
    )
    
    embedding = models.TextField(
        blank=True,
        verbose_name=_("Embedding"),
        help_text=_("Vector embedding for similarity search"),
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata for the chunk"),
    )
    
    def __str__(self):
        """Return string representation of the evidence chunk."""
        return f"Chunk {self.chunk_index} of {self.source.title}"


class EvidenceInsight(BaseModel, TaggableMixin):
    """
    Evidence insight model for storing AI-generated insights.
    
    Represents higher-level insights and patterns identified from evidence facts.
    Maps to "Insights" in specification.
    """
    
    # Define PII fields as a class attribute
    pii_fields = ["title", "notes"]
    
    class Meta:
        verbose_name = _("Evidence Insight")
        verbose_name_plural = _("Evidence Insights")
        indexes = [
            models.Index(fields=["organization", "evidence_score"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["sentiment"]),
        ]
    
    class PriorityChoices(models.TextChoices):
        """Enumeration of priority levels."""
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
    
    class SentimentChoices(models.TextChoices):
        """Enumeration of sentiment options."""
        POSITIVE = "positive", _("Positive")
        NEUTRAL = "neutral", _("Neutral")
        NEGATIVE = "negative", _("Negative")
    
    # Organization field (required for multi-tenancy and RBAC)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="evidence_insights",
        help_text=_("Organization this evidence insight belongs to"),
    )
    
    # Projects can be multiple (optional)
    projects = models.ManyToManyField(
        "core.Project",
        blank=True,
        related_name="evidence_insights",
        verbose_name=_("Projects"),
        help_text=_("Projects this insight belongs to (optional, can be multiple)"),
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Title of the evidence insight"),
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional context; expandable"),
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        verbose_name=_("Priority"),
        help_text=_("Priority level of this insight"),
    )
    
    # Supporting Evidence: Observations tied to this insight
    supporting_evidence = models.ManyToManyField(
        "core.EvidenceFact",
        blank=True,
        related_name="insights",
        verbose_name=_("Supporting Evidence"),
        help_text=_("Observations tied to this insight"),
    )
    
    evidence_score = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Evidence Score"),
        help_text=_("1-2: Limited Evidence, 3-5: Moderate Evidence, 6+: High Evidence"),
    )
    
    sentiment = models.CharField(
        max_length=20,
        choices=SentimentChoices.choices,
        null=True,
        blank=True,
        verbose_name=_("Sentiment"),
        help_text=_("Sentiment analysis of the insight (optional)"),
    )
    
    # Legacy field for backward compatibility
    tags_list = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Tags List"),
        help_text=_("Legacy list of tag names for this insight"),
    )

    # Tags relationship - global repository tags
    tags = models.ManyToManyField(
        "core.Tag",
        blank=True,
        related_name="evidence_insights",
        verbose_name=_("Tags"),
        help_text=_("Global repository tags")
    )
    
    def clean(self):
        """Validate evidence score range."""
        super().clean()
        if self.evidence_score is not None and self.evidence_score < 1:
            raise ValidationError({"evidence_score": _("Evidence score must be at least 1.")})
    
    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def evidence_level(self):
        """Get human-readable evidence level based on score."""
        if self.evidence_score <= 2:
            return _("Limited Evidence")
        elif self.evidence_score <= 5:
            return _("Moderate Evidence")
        else:
            return _("High Evidence")
    
    def __str__(self):
        """Return string representation of the evidence insight."""
        return f"{self.title} ({self.organization.name})"


class Recommendation(BaseModel, TaggableMixin):
    """
    Recommendation model for storing AI-generated recommendations.
    
    Represents actionable recommendations based on evidence insights.
    """
    
    # Define PII fields as a class attribute
    pii_fields = ["title", "notes"]
    
    class Meta:
        verbose_name = _("Recommendation")
        verbose_name_plural = _("Recommendations")
        indexes = [
            models.Index(fields=["organization", "type"]),
            models.Index(fields=["effort", "impact"]),
            models.Index(fields=["status"]),
        ]
    
    class EffortChoices(models.TextChoices):
        """Enumeration of effort levels."""
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
    
    class ImpactChoices(models.TextChoices):
        """Enumeration of impact levels."""
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
    
    class TypeChoices(models.TextChoices):
        """Enumeration of recommendation types."""
        OPPORTUNITY = "opportunity", _("Opportunity")
        SOLUTION = "solution", _("Solution")
    
    class StatusChoices(models.TextChoices):
        """Enumeration of configurable checkbox statuses."""
        NOT_STARTED = "not_started", _("Not Started")
        IN_DISCOVERY = "in_discovery", _("In Discovery")
        IN_DELIVERY = "in_delivery", _("In Delivery")
        COMPLETED = "completed", _("Completed")
        WONT_DO = "wont_do", _("Won't Do")
    
    # Organization field (required for multi-tenancy and RBAC)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="recommendations",
        help_text=_("Organization this recommendation belongs to"),
    )
    
    # Projects can be multiple (optional, inferred from insights)
    projects = models.ManyToManyField(
        "core.Project",
        blank=True,
        related_name="recommendations",
        verbose_name=_("Projects"),
        help_text=_("Projects this recommendation belongs to (optional, can be multiple)"),
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Title of the recommendation"),
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional context; expandable"),
    )
    
    effort = models.CharField(
        max_length=20,
        choices=EffortChoices.choices,
        default=EffortChoices.MEDIUM,
        verbose_name=_("Effort"),
        help_text=_("Estimated effort required to implement"),
    )
    
    impact = models.CharField(
        max_length=20,
        choices=ImpactChoices.choices,
        default=ImpactChoices.MEDIUM,
        verbose_name=_("Impact"),
        help_text=_("Expected impact of this recommendation"),
    )
    
    type = models.CharField(
        max_length=20,
        choices=TypeChoices.choices,
        default=TypeChoices.OPPORTUNITY,
        verbose_name=_("Type"),
        help_text=_("Type of recommendation: Opportunity or Solution"),
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NOT_STARTED,
        verbose_name=_("Status"),
        help_text=_("Configurable checkbox status"),
    )
    
    # Supporting Evidence: Insights tied to this recommendation
    supporting_evidence = models.ManyToManyField(
        "core.EvidenceInsight",
        blank=True,
        related_name="recommendations",
        verbose_name=_("Supporting Evidence"),
        help_text=_("Insights tied to this recommendation"),
    )
    
    evidence_score = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Evidence Score"),
        help_text=_("Based on sum of associated insight evidence scores (1-2: Limited, 3-5: Moderate, 6+: High)"),
    )
    
    # Legacy field for backward compatibility
    tags_list = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Tags List"),
        help_text=_("Legacy list of tag names for this recommendation"),
    )

    # Tags relationship - global repository tags
    tags = models.ManyToManyField(
        "core.Tag",
        blank=True,
        related_name="recommendations",
        verbose_name=_("Tags"),
        help_text=_("Global repository tags")
    )
    
    def clean(self):
        """Validate evidence score range."""
        super().clean()
        if self.evidence_score is not None and self.evidence_score < 1:
            raise ValidationError({"evidence_score": _("Evidence score must be at least 1.")})
    
    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def evidence_level(self):
        """Get human-readable evidence level based on score."""
        if self.evidence_score <= 2:
            return _("Limited Evidence")
        elif self.evidence_score <= 5:
            return _("Moderate Evidence")
        else:
            return _("High Evidence")
    
    def __str__(self):
        """Return string representation of the recommendation."""
        return f"{self.title} ({self.organization.name})"
