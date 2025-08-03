"""
Multi-cloud storage backends for Django.

This package provides abstract storage interfaces and implementations for
various cloud providers to reduce vendor lock-in.
"""

from .base import CloudStorageInterface, BaseCloudStorage, OrganizationScopedStorageMixin, CloudStorageFactory
from .gcs import GCSStorage, OrganizationScopedGCSStorage
from .s3 import S3Storage, OrganizationScopedS3Storage
from .azure import AzureBlobStorage, OrganizationScopedAzureBlobStorage

__all__ = [
    'CloudStorageInterface',
    'BaseCloudStorage', 
    'OrganizationScopedStorageMixin',
    'CloudStorageFactory',
    'GCSStorage',
    'OrganizationScopedGCSStorage',
    'S3Storage', 
    'OrganizationScopedS3Storage',
    'AzureBlobStorage',
    'OrganizationScopedAzureBlobStorage',
]

# Convenience function to get the configured storage backend
def get_default_storage():
    """
    Get the default storage backend based on Django settings.
    
    Returns:
        Storage backend instance
    """
    from django.conf import settings
    
    provider = getattr(settings, 'CLOUD_STORAGE_PROVIDER', 'gcs')
    use_org_scoping = getattr(settings, 'CLOUD_STORAGE_USE_ORG_SCOPING', True)
    
    if use_org_scoping:
        provider += '_org'
    
    # Get provider-specific configuration
    config = {}
    
    if provider.startswith('gcs'):
        config.update({
            'bucket_name': getattr(settings, 'CLOUD_STORAGE_BUCKET_NAME', None),
            'client_options': getattr(settings, 'GCS_CLIENT_OPTIONS', {}),
            'use_emulator': getattr(settings, 'USE_GCS_EMULATOR', False),
        })
    elif provider.startswith('s3'):
        config.update({
            'bucket_name': getattr(settings, 'CLOUD_STORAGE_BUCKET_NAME', None),
            'region': getattr(settings, 'AWS_S3_REGION', None),
            'access_key_id': getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            'secret_access_key': getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            'endpoint_url': getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
        })
    elif provider.startswith('azure'):
        config.update({
            'container_name': getattr(settings, 'CLOUD_STORAGE_BUCKET_NAME', None),
            'account_name': getattr(settings, 'AZURE_ACCOUNT_NAME', None),
            'account_key': getattr(settings, 'AZURE_ACCOUNT_KEY', None),
            'connection_string': getattr(settings, 'AZURE_CONNECTION_STRING', None),
            'sas_token': getattr(settings, 'AZURE_SAS_TOKEN', None),
        })
    
    return CloudStorageFactory.create_storage(provider, **config)