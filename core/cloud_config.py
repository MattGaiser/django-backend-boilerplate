"""
Cloud provider configuration abstraction layer.

This module provides a unified configuration interface that maps generic
cloud service settings to provider-specific configurations.
"""

from typing import Dict, Any, Optional
from django.conf import settings
from decouple import config


class CloudConfig:
    """
    Abstract configuration manager for cloud services.
    
    Provides a unified interface for configuring different cloud providers
    without exposing provider-specific implementation details.
    """

    def __init__(self):
        self.provider = config('CLOUD_PROVIDER', default='gcp')
        self.environment = config('DJANGO_ENV', default='development')

    @property
    def storage_config(self) -> Dict[str, Any]:
        """Get storage configuration for the active cloud provider."""
        if self.provider == 'gcp':
            return self._get_gcp_storage_config()
        elif self.provider == 'aws':
            return self._get_aws_storage_config()
        elif self.provider == 'azure':
            return self._get_azure_storage_config()
        else:
            raise ValueError(f"Unsupported cloud provider: {self.provider}")

    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration for the active cloud provider."""
        if self.provider == 'gcp':
            return self._get_gcp_database_config()
        elif self.provider == 'aws':
            return self._get_aws_database_config()
        elif self.provider == 'azure':
            return self._get_azure_database_config()
        else:
            raise ValueError(f"Unsupported cloud provider: {self.provider}")

    @property
    def secrets_config(self) -> Dict[str, Any]:
        """Get secrets management configuration for the active cloud provider."""
        if self.provider == 'gcp':
            return self._get_gcp_secrets_config()
        elif self.provider == 'aws':
            return self._get_aws_secrets_config()
        elif self.provider == 'azure':
            return self._get_azure_secrets_config()
        else:
            raise ValueError(f"Unsupported cloud provider: {self.provider}")

    def _get_gcp_storage_config(self) -> Dict[str, Any]:
        """Get Google Cloud Storage configuration."""
        return {
            'provider': 'gcs',
            'bucket_name': config('CLOUD_STORAGE_BUCKET_NAME', default='dev-app-assets'),
            'use_emulator': config('USE_GCS_EMULATOR', default=False, cast=bool),
            'emulator_host': config('GCS_EMULATOR_HOST', default='http://fake-gcs-server:9090'),
            'project_id': config('GCP_PROJECT_ID', default=''),
            'credentials_path': config('GOOGLE_APPLICATION_CREDENTIALS', default=''),
        }

    def _get_aws_storage_config(self) -> Dict[str, Any]:
        """Get AWS S3 configuration."""
        return {
            'provider': 's3',
            'bucket_name': config('CLOUD_STORAGE_BUCKET_NAME', default='dev-app-assets'),
            'region': config('AWS_DEFAULT_REGION', default='us-east-1'),
            'access_key_id': config('AWS_ACCESS_KEY_ID', default=''),
            'secret_access_key': config('AWS_SECRET_ACCESS_KEY', default=''),
            'endpoint_url': config('AWS_S3_ENDPOINT_URL', default=None),
            'use_ssl': config('AWS_S3_USE_SSL', default=True, cast=bool),
        }

    def _get_azure_storage_config(self) -> Dict[str, Any]:
        """Get Azure Blob Storage configuration."""
        return {
            'provider': 'azure',
            'container_name': config('CLOUD_STORAGE_BUCKET_NAME', default='dev-app-assets'),
            'account_name': config('AZURE_STORAGE_ACCOUNT_NAME', default=''),
            'account_key': config('AZURE_STORAGE_ACCOUNT_KEY', default=''),
            'connection_string': config('AZURE_STORAGE_CONNECTION_STRING', default=''),
            'sas_token': config('AZURE_STORAGE_SAS_TOKEN', default=''),
        }

    def _get_gcp_database_config(self) -> Dict[str, Any]:
        """Get Google Cloud SQL configuration."""
        if config('USE_POSTGRES', default=False, cast=bool):
            return {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('POSTGRES_DB', default='django_db'),
                'USER': config('POSTGRES_USER', default='django_user'),
                'PASSWORD': config('POSTGRES_PASSWORD', default='django_password'),
                'HOST': config('POSTGRES_HOST', default='db'),
                'PORT': config('POSTGRES_PORT', default='5432'),
                'OPTIONS': {
                    'sslmode': config('POSTGRES_SSL_MODE', default='prefer'),
                },
            }
        else:
            return {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': config('DATABASE_PATH', default='db.sqlite3'),
            }

    def _get_aws_database_config(self) -> Dict[str, Any]:
        """Get AWS RDS configuration."""
        if config('USE_POSTGRES', default=False, cast=bool):
            return {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('RDS_DB_NAME', default='django_db'),
                'USER': config('RDS_USERNAME', default='django_user'),
                'PASSWORD': config('RDS_PASSWORD', default='django_password'),
                'HOST': config('RDS_HOSTNAME', default='localhost'),
                'PORT': config('RDS_PORT', default='5432'),
                'OPTIONS': {
                    'sslmode': config('RDS_SSL_MODE', default='require'),
                },
            }
        else:
            return {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': config('DATABASE_PATH', default='db.sqlite3'),
            }

    def _get_azure_database_config(self) -> Dict[str, Any]:
        """Get Azure Database for PostgreSQL configuration."""
        if config('USE_POSTGRES', default=False, cast=bool):
            return {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('AZURE_DB_NAME', default='django_db'),
                'USER': config('AZURE_DB_USER', default='django_user'),
                'PASSWORD': config('AZURE_DB_PASSWORD', default='django_password'),
                'HOST': config('AZURE_DB_HOST', default='localhost'),
                'PORT': config('AZURE_DB_PORT', default='5432'),
                'OPTIONS': {
                    'sslmode': config('AZURE_DB_SSL_MODE', default='require'),
                },
            }
        else:
            return {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': config('DATABASE_PATH', default='db.sqlite3'),
            }

    def _get_gcp_secrets_config(self) -> Dict[str, Any]:
        """Get Google Secret Manager configuration."""
        return {
            'provider': 'gcp_secret_manager',
            'project_id': config('GCP_PROJECT_ID', default=''),
            'credentials_path': config('GOOGLE_APPLICATION_CREDENTIALS', default=''),
        }

    def _get_aws_secrets_config(self) -> Dict[str, Any]:
        """Get AWS Systems Manager Parameter Store configuration."""
        return {
            'provider': 'aws_parameter_store',
            'region': config('AWS_DEFAULT_REGION', default='us-east-1'),
            'access_key_id': config('AWS_ACCESS_KEY_ID', default=''),
            'secret_access_key': config('AWS_SECRET_ACCESS_KEY', default=''),
        }

    def _get_azure_secrets_config(self) -> Dict[str, Any]:
        """Get Azure Key Vault configuration."""
        return {
            'provider': 'azure_key_vault',
            'vault_url': config('AZURE_KEY_VAULT_URL', default=''),
            'client_id': config('AZURE_CLIENT_ID', default=''),
            'client_secret': config('AZURE_CLIENT_SECRET', default=''),
            'tenant_id': config('AZURE_TENANT_ID', default=''),
        }

    def get_oauth_providers(self) -> Dict[str, Any]:
        """Get OAuth provider configuration."""
        providers = {}
        
        # Google OAuth (works with all cloud providers)
        google_client_id = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
        google_client_secret = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')
        if google_client_id and google_client_secret:
            providers['google'] = {
                'SCOPE': ['profile', 'email'],
                'AUTH_PARAMS': {'access_type': 'online'},
                'OAUTH_PKCE_ENABLED': True,
                'APP': {
                    'client_id': google_client_id,
                    'secret': google_client_secret,
                    'key': '',
                }
            }
        
        # Microsoft OAuth (works with all cloud providers, but commonly used with Azure)
        microsoft_client_id = config('MICROSOFT_OAUTH2_CLIENT_ID', default='')
        microsoft_client_secret = config('MICROSOFT_OAUTH2_CLIENT_SECRET', default='')
        if microsoft_client_id and microsoft_client_secret:
            providers['microsoft'] = {
                'SCOPE': ['User.Read', 'email'],
                'APP': {
                    'client_id': microsoft_client_id,
                    'secret': microsoft_client_secret,
                    'key': '',
                }
            }
        
        # AWS Cognito (when using AWS)
        if self.provider == 'aws':
            cognito_client_id = config('AWS_COGNITO_CLIENT_ID', default='')
            cognito_client_secret = config('AWS_COGNITO_CLIENT_SECRET', default='')
            cognito_domain = config('AWS_COGNITO_DOMAIN', default='')
            if cognito_client_id and cognito_domain:
                providers['cognito'] = {
                    'APP': {
                        'client_id': cognito_client_id,
                        'secret': cognito_client_secret,
                    },
                    'DOMAIN': cognito_domain,
                }
        
        return providers

    def get_cors_origins(self) -> list:
        """Get CORS allowed origins based on environment."""
        if self.environment == 'development':
            return [
                'http://localhost:3000',
                'http://127.0.0.1:3000',
                'http://0.0.0.0:3000',
            ]
        else:
            # Production origins - should be configured via environment
            origins = config('CORS_ALLOWED_ORIGINS', default='')
            return origins.split(',') if origins else []

    def get_allowed_hosts(self) -> list:
        """Get allowed hosts based on cloud provider and environment."""
        hosts = []
        
        if self.environment == 'development':
            hosts.extend(['localhost', '127.0.0.1', '0.0.0.0', 'testserver'])
        
        # Add cloud provider specific hosts
        if self.provider == 'gcp':
            hosts.append('*.run.app')  # Cloud Run domains
        elif self.provider == 'aws':
            hosts.append('*.amazonaws.com')  # ELB/ALB domains
            hosts.append('*.elasticbeanstalk.com')  # Elastic Beanstalk domains
        elif self.provider == 'azure':
            hosts.append('*.azurewebsites.net')  # App Service domains
            hosts.append('*.cloudapp.azure.com')  # VM domains
        
        # Add custom domains from environment
        custom_hosts = config('ALLOWED_HOSTS', default='')
        if custom_hosts:
            hosts.extend(custom_hosts.split(','))
        
        return hosts


# Global configuration instance
cloud_config = CloudConfig()