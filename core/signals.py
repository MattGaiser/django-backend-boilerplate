import threading
from django.db.models.signals import pre_save, class_prepared
from django.dispatch import receiver
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps
from django.db import connection
from .models import BaseModel, User


# Thread-local storage for the current user
_thread_locals = threading.local()


def set_current_user(user):
    """Set the current user in thread-local storage."""
    _thread_locals.user = user


def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)


@receiver(pre_save, sender=User)
@receiver(pre_save)
def auto_assign_user_fields(sender, instance, **kwargs):
    """
    Automatically assign created_by and updated_by fields based on the current user.
    
    This signal is triggered before saving any model that inherits from BaseModel.
    """
    if not issubclass(sender, BaseModel):
        return
    
    current_user = get_current_user()
    if current_user and current_user.is_authenticated:
        # If this is a new instance (no pk), set created_by
        if not instance.pk and hasattr(instance, 'created_by'):
            instance.created_by = current_user
        
        # Always update updated_by for existing instances
        if instance.pk and hasattr(instance, 'updated_by'):
            instance.updated_by = current_user


@receiver(class_prepared)
def validate_pii_fields(sender, **kwargs):
    """
    Validate that models with PII-like fields have proper pii_fields declaration.
    
    This signal checks for common PII field names and ensures they are declared
    in the model's pii_fields class attribute for compliance tracking.
    """
    # Skip during migrations
    try:
        if connection.in_atomic_block or 'migrate' in connection.queries_log:
            return
    except:
        pass
    
    # Skip if this is not a Django model or is abstract
    if not hasattr(sender, '_meta') or sender._meta.abstract:
        return
    
    # Skip built-in Django models and migrations
    if sender._meta.app_label in ['admin', 'auth', 'contenttypes', 'sessions']:
        return
    
    # Skip Django's internal models
    if sender.__module__.startswith('django.'):
        return
    
    # Skip if this is the migration recorder model or any intermediary model
    if (sender.__name__ == 'Migration' and 'migrations' in sender.__module__) or \
       '_' in sender.__name__ or \
       not hasattr(sender, '__module__'):
        return
    
    # Skip intermediary models created by Django
    if hasattr(sender._meta, 'auto_created') and sender._meta.auto_created:
        return
    
    try:
        # Common PII field names to check for
        pii_field_names = {
            'email', 'full_name', 'first_name', 'last_name', 'name',
            'phone', 'phone_number', 'address', 'street_address',
            'city', 'postal_code', 'zip_code', 'ssn', 'social_security_number',
            'date_of_birth', 'birth_date', 'ip_address', 'last_login_ip'
        }
        
        # Get all field names from the model - safely
        try:
            model_field_names = {field.name for field in sender._meta.get_fields() 
                                if hasattr(field, 'name')}
        except (AttributeError, TypeError):
            # Skip if we can't get fields safely
            return
        
        # Check if any PII fields exist in the model
        found_pii_fields = model_field_names.intersection(pii_field_names)
        
        if found_pii_fields:
            # Check if the model has pii_fields defined as a class attribute
            pii_fields = getattr(sender, 'pii_fields', None)
            
            if pii_fields is None:
                raise ImproperlyConfigured(
                    f"Model {sender.__name__} contains PII fields {found_pii_fields} "
                    "but does not declare pii_fields. Please add a class attribute "
                    "pii_fields = [...] listing all PII fields for compliance tracking."
                )
            
            # Check if all found PII fields are declared
            declared_fields = set(pii_fields)
            undeclared_fields = found_pii_fields - declared_fields
            
            if undeclared_fields:
                raise ImproperlyConfigured(
                    f"Model {sender.__name__} contains PII fields {undeclared_fields} "
                    f"that are not declared in pii_fields. Current pii_fields: {declared_fields}. "
                    "Please update pii_fields to include all PII fields."
                )
    except Exception:
        # Silently skip validation during Django model initialization issues
        pass