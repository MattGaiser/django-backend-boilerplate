from django.db import models
from django.utils.translation import gettext_lazy as _


class OrgRole(models.TextChoices):
    """Enumeration of organization roles for role-based access control."""
    ADMIN = "admin", _("Admin")
    MANAGER = "manager", _("Manager")
    EDITOR = "editor", _("Editor")
    VIEWER = "viewer", _("Viewer")
    SUPER_ADMIN = "super_admin", _("Super Admin")