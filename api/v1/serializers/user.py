"""
User serializers for API responses.

Provides serialization for User model with proper PII handling and translation support.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import OrganizationMembership, User


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.

    Includes basic user information with PII fields appropriately handled.
    Note: PII fields are marked in the model's pii_fields attribute.
    """

    full_name = serializers.CharField(
        max_length=150, help_text=_("Full name of the user")
    )

    email = serializers.EmailField(
        read_only=True,  # Email should not be editable through this endpoint
        help_text=_("Email address (read-only)"),
    )

    language = serializers.CharField(
        max_length=10, default="en", help_text=_("Preferred language code")
    )

    timezone = serializers.CharField(
        max_length=50, default="UTC", help_text=_("User's timezone")
    )

    date_joined = serializers.DateTimeField(
        read_only=True, help_text=_("Date when the user joined")
    )

    is_active = serializers.BooleanField(
        read_only=True, help_text=_("Whether the user account is active")
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "language",
            "timezone",
            "date_joined",
            "is_active",
        ]
        read_only_fields = ["id", "email", "date_joined", "is_active"]

    def validate_full_name(self, value):
        """
        Validate full name field.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(_("Full name cannot be empty."))

        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                _("Full name must be at least 2 characters long.")
            )

        return value.strip()

    def validate_language(self, value):
        """
        Validate language code.
        """
        # Basic validation for language codes
        if value and len(value) > 10:
            raise serializers.ValidationError(_("Language code is too long."))

        return value

    def validate_timezone(self, value):
        """
        Validate timezone string.
        """
        if value and len(value) > 50:
            raise serializers.ValidationError(_("Timezone string is too long."))

        return value


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for organization membership information.
    """

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        help_text=_("Name of the organization"),
    )

    organization_id = serializers.UUIDField(
        source="organization.id", read_only=True, help_text=_("ID of the organization")
    )

    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
        help_text=_("Human-readable role name"),
    )

    class Meta:
        model = OrganizationMembership
        fields = [
            "organization_id",
            "organization_name",
            "role",
            "role_display",
            "is_default",
        ]
        read_only_fields = ["organization_id", "organization_name", "role_display"]


class UserWithOrganizationsSerializer(UserProfileSerializer):
    """
    Extended user serializer that includes organization memberships.

    Used for endpoints like /me/ where complete user context is needed.
    """

    organizations = OrganizationMembershipSerializer(
        source="organization_memberships",
        many=True,
        read_only=True,
        help_text=_("Organizations this user belongs to"),
    )

    default_organization = serializers.SerializerMethodField(
        help_text=_("User's default organization")
    )

    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + [
            "organizations",
            "default_organization",
        ]

    def get_default_organization(self, obj):
        """
        Get the user's default organization information.
        """
        default_org = obj.get_default_organization()
        if default_org:
            return {"id": default_org.id, "name": default_org.name}
        return None


class CreateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.

    Includes password handling and validation.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text=_("Password for the new user (minimum 8 characters)"),
    )

    password_confirm = serializers.CharField(
        write_only=True, help_text=_("Password confirmation")
    )

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "password",
            "password_confirm",
            "language",
            "timezone",
        ]

    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        password = attrs.get("password")
        password_confirm = attrs.pop("password_confirm", None)

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )

        return attrs

    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
