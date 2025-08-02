import threading
import logging
from django.db.models.signals import pre_save, class_prepared
from django.dispatch import receiver
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps
from django.db import connection
from django.conf import settings
from .models import BaseModel, User


# Thread-local storage for the current user
_thread_locals = threading.local()

# Configure logging
logger = logging.getLogger(__name__)


def get_pii_field_names():
    """
    Get the list of field names that are considered PII.
    
    Can be configured via Django settings CORE_PII_FIELD_NAMES.
    """
    return getattr(settings, 'CORE_PII_FIELD_NAMES', {
        'email', 'full_name', 'first_name', 'last_name', 'name',
        'phone', 'phone_number', 'address', 'street_address',
        'city', 'postal_code', 'zip_code', 'ssn', 'social_security_number',
        'date_of_birth', 'birth_date', 'ip_address', 'last_login_ip'
    })


def get_model_pii_fields(model):
    """
    Helper to introspect and return all pii_fields for any model.
    
    Args:
        model: Django model class
        
    Returns:
        list: List of PII field names declared in the model's pii_fields attribute,
              or empty list if not declared
    """
    return getattr(model, 'pii_fields', [])


def get_model_field_names(model):
    """
    Safely get all field names from a model.
    
    Args:
        model: Django model class
        
    Returns:
        set: Set of field names, or empty set if unable to retrieve
    """
    try:
        return {field.name for field in model._meta.get_fields() 
                if hasattr(field, 'name')}
    except (AttributeError, TypeError):
        return set()


def set_current_user(user):
    """Set the current user in thread-local storage."""
    _thread_locals.user = user


def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)


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
        # Check if this is a new instance by checking the _state.adding attribute
        # or using kwargs.get('created', True) fallback
        is_new_instance = getattr(instance, '_state', None) and instance._state.adding
        
        # If this is a new instance, set created_by
        if is_new_instance and hasattr(instance, 'created_by'):
            instance.created_by = current_user
        
        # Always update updated_by for all saves (both create and update)
        if hasattr(instance, 'updated_by'):
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
        # Get configurable PII field names
        pii_field_names = get_pii_field_names()
        
        # Get all field names from the model - safely
        model_field_names = get_model_field_names(sender)
        if not model_field_names:
            return
        
        # Check if any PII fields exist in the model
        found_pii_fields = model_field_names.intersection(pii_field_names)
        
        if found_pii_fields:
            # Check if the model has pii_fields defined as a class attribute
            declared_pii_fields = get_model_pii_fields(sender)
            
            if declared_pii_fields is None:
                raise ImproperlyConfigured(
                    f"Model {sender.__name__} contains PII fields {found_pii_fields} "
                    "but does not declare pii_fields. Please add a class attribute "
                    "pii_fields = [...] listing all PII fields for compliance tracking."
                )
            
            # Check if all found PII fields are declared
            declared_fields = set(declared_pii_fields)
            undeclared_fields = found_pii_fields - declared_fields
            
            if undeclared_fields:
                raise ImproperlyConfigured(
                    f"Model {sender.__name__} contains PII fields {undeclared_fields} "
                    f"that are not declared in pii_fields. Current pii_fields: {declared_fields}. "
                    "Please update pii_fields to include all PII fields."
                )
            
            # Log warnings for potential ambiguous PII detection
            ambiguous_fields = model_field_names.intersection({
                'name', 'title', 'description', 'content', 'note', 'comment'
            })
            
            ambiguous_undeclared = ambiguous_fields - declared_fields
            if ambiguous_undeclared:
                logger.warning(
                    f"Model {sender.__name__} has fields {ambiguous_undeclared} "
                    "that might contain PII but are not declared in pii_fields. "
                    "Please review if these fields should be included in pii_fields."
                )
                
    except Exception as e:
        # Log the exception but don't break Django startup
        logger.debug(f"PII validation skipped for {sender.__name__}: {e}")
        pass