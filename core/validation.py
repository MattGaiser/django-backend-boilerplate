"""
Environment validation utilities for the Django Backend Boilerplate.

Provides validation for environment variables and configuration
to ensure proper setup across different deployment environments.
"""

import os
import sys
from typing import Dict, List, Optional, Union

import structlog
from django.conf import settings
from django.core.management.color import color_style
from pydantic import BaseModel, Field, ValidationError, validator

logger = structlog.get_logger(__name__)
style = color_style()


class DatabaseConfig(BaseModel):
    """Database configuration validation."""
    
    postgres_db: str = Field(..., min_length=1, description="PostgreSQL database name")
    postgres_user: str = Field(..., min_length=1, description="PostgreSQL username")
    postgres_password: str = Field(..., min_length=8, description="PostgreSQL password")
    postgres_host: str = Field(default="db", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    
    @validator("postgres_password")
    def validate_password_strength(cls, v):
        """Validate password has minimum complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # In production, require stronger passwords
        django_env = os.getenv("DJANGO_ENV", "development")
        if django_env == "production":
            if not any(c.isupper() for c in v):
                raise ValueError("Production password must contain uppercase letters")
            if not any(c.islower() for c in v):
                raise ValueError("Production password must contain lowercase letters")
            if not any(c.isdigit() for c in v):
                raise ValueError("Production password must contain digits")
        
        return v


class SecurityConfig(BaseModel):
    """Security configuration validation."""
    
    secret_key: str = Field(..., min_length=50, description="Django secret key")
    allowed_hosts: List[str] = Field(default=["localhost"], description="Allowed hosts")
    debug: bool = Field(default=False, description="Debug mode")
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Validate secret key is not the default."""
        default_keys = [
            "django-insecure-2%l-xabc_5q%*ch4c+_s4z12)fopd!cl2(h$6t(hj24glyd)nk",
            "your-secret-key-here",
            "change-me",
            "insecure-key",
        ]
        
        if v in default_keys:
            raise ValueError("Secret key must be changed from default value")
        
        if len(v) < 50:
            raise ValueError("Secret key must be at least 50 characters long")
        
        return v
    
    @validator("allowed_hosts")
    def validate_allowed_hosts(cls, v, values):
        """Validate allowed hosts for production."""
        django_env = os.getenv("DJANGO_ENV", "development")
        debug = values.get("debug", False)
        
        if django_env == "production" and debug:
            raise ValueError("Debug mode must be disabled in production")
        
        if django_env in ["production", "staging"]:
            if not v or v == ["localhost"]:
                raise ValueError(f"Allowed hosts must be configured for {django_env}")
            
            # Check for wildcard in production
            if "*" in v and django_env == "production":
                raise ValueError("Wildcard in ALLOWED_HOSTS is not secure for production")
        
        return v


class SSOConfig(BaseModel):
    """SSO configuration validation."""
    
    google_client_id: Optional[str] = Field(default="", description="Google OAuth2 client ID")
    google_client_secret: Optional[str] = Field(default="", description="Google OAuth2 client secret")
    azure_client_id: Optional[str] = Field(default="", description="Azure AD client ID")
    azure_client_secret: Optional[str] = Field(default="", description="Azure AD client secret")
    
    @validator("google_client_id", "azure_client_id")
    def validate_client_id_format(cls, v):
        """Validate client ID format."""
        if v and not v.startswith(("your-", "placeholder-", "demo-")):
            # Basic format validation for real client IDs
            if "google" in cls.__fields__ and len(v) > 0 and not v.endswith(".apps.googleusercontent.com"):
                if not v.startswith("GOCSPX-"):  # Could be Google client ID or secret
                    logger.warning("Google client ID should end with .apps.googleusercontent.com")
        
        return v
    
    @validator("google_client_secret", "azure_client_secret")
    def validate_client_secret(cls, v):
        """Validate client secret is not placeholder."""
        placeholder_values = [
            "your-google-client-secret",
            "your-azure-ad-client-secret",
            "placeholder-secret",
            "change-me",
        ]
        
        if v in placeholder_values:
            logger.warning("SSO client secret appears to be a placeholder value")
        
        return v


class CacheConfig(BaseModel):
    """Cache configuration validation."""
    
    use_redis: bool = Field(default=False, description="Whether to use Redis cache")
    redis_url: Optional[str] = Field(default="", description="Redis connection URL")
    cache_key_prefix: str = Field(default="djboiler", description="Cache key prefix")
    
    @validator("redis_url")
    def validate_redis_url(cls, v, values):
        """Validate Redis URL if Redis is enabled."""
        use_redis = values.get("use_redis", False)
        
        if use_redis and not v:
            raise ValueError("Redis URL is required when USE_REDIS_CACHE is True")
        
        if v and not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        
        return v


class EnvironmentConfig(BaseModel):
    """Complete environment configuration validation."""
    
    django_env: str = Field(default="development", description="Django environment")
    database: DatabaseConfig
    security: SecurityConfig
    sso: SSOConfig = Field(default_factory=SSOConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    
    @validator("django_env")
    def validate_environment(cls, v):
        """Validate environment name."""
        valid_environments = ["development", "test", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_environments}")
        return v


class EnvironmentValidator:
    """
    Comprehensive environment validation utility.
    
    Validates environment variables and configuration for different deployment environments.
    """
    
    def __init__(self):
        """Initialize environment validator."""
        self.errors = []
        self.warnings = []
        self.django_env = os.getenv("DJANGO_ENV", "development")
    
    def validate_all(self) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate all environment configuration.
        
        Returns:
            dict: Validation results with success status and any errors/warnings
        """
        self.errors = []
        self.warnings = []
        
        # Basic environment variables
        self._validate_basic_env_vars()
        
        # Environment-specific validation
        if self.django_env == "production":
            self._validate_production_env()
        elif self.django_env == "staging":
            self._validate_staging_env()
        elif self.django_env == "test":
            self._validate_test_env()
        
        # Configuration validation using Pydantic
        self._validate_configuration()
        
        # Security checks
        self._validate_security_settings()
        
        return {
            "success": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "environment": self.django_env,
        }
    
    def _validate_basic_env_vars(self):
        """Validate basic required environment variables."""
        required_vars = [
            "SECRET_KEY",
            "DJANGO_ENV",
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var}")
    
    def _validate_production_env(self):
        """Validate production-specific requirements."""
        production_required = [
            "POSTGRES_DB",
            "POSTGRES_USER", 
            "POSTGRES_PASSWORD",
            "POSTGRES_HOST",
            "ALLOWED_HOSTS",
        ]
        
        for var in production_required:
            if not os.getenv(var):
                self.errors.append(f"Missing required production environment variable: {var}")
        
        # Production-specific checks
        if os.getenv("DEBUG", "false").lower() == "true":
            self.errors.append("DEBUG must be False in production")
        
        # Check SSL/HTTPS settings
        if not os.getenv("SECURE_SSL_REDIRECT", "false").lower() == "true":
            self.warnings.append("Consider enabling SECURE_SSL_REDIRECT for production HTTPS")
    
    def _validate_staging_env(self):
        """Validate staging-specific requirements."""
        staging_required = [
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "ALLOWED_HOSTS",
        ]
        
        for var in staging_required:
            if not os.getenv(var):
                self.errors.append(f"Missing required staging environment variable: {var}")
    
    def _validate_test_env(self):
        """Validate test environment configuration."""
        # Test environment should use simplified settings
        if os.getenv("USE_POSTGRES", "false").lower() == "true":
            test_db_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
            for var in test_db_vars:
                if not os.getenv(var):
                    self.warnings.append(f"PostgreSQL enabled but missing: {var}")
    
    def _validate_configuration(self):
        """Validate configuration using Pydantic models."""
        try:
            # Prepare configuration data
            config_data = {
                "django_env": self.django_env,
                "database": {
                    "postgres_db": os.getenv("POSTGRES_DB", ""),
                    "postgres_user": os.getenv("POSTGRES_USER", ""),
                    "postgres_password": os.getenv("POSTGRES_PASSWORD", ""),
                    "postgres_host": os.getenv("POSTGRES_HOST", "db"),
                    "postgres_port": int(os.getenv("POSTGRES_PORT", "5432")),
                },
                "security": {
                    "secret_key": os.getenv("SECRET_KEY", ""),
                    "allowed_hosts": os.getenv("ALLOWED_HOSTS", "localhost").split(","),
                    "debug": os.getenv("DEBUG", "false").lower() == "true",
                },
                "sso": {
                    "google_client_id": os.getenv("GOOGLE_OAUTH2_CLIENT_ID", ""),
                    "google_client_secret": os.getenv("GOOGLE_OAUTH2_CLIENT_SECRET", ""),
                    "azure_client_id": os.getenv("AZURE_AD_CLIENT_ID", ""),
                    "azure_client_secret": os.getenv("AZURE_AD_CLIENT_SECRET", ""),
                },
                "cache": {
                    "use_redis": os.getenv("USE_REDIS_CACHE", "false").lower() == "true",
                    "redis_url": os.getenv("REDIS_URL", ""),
                    "cache_key_prefix": os.getenv("CACHE_KEY_PREFIX", "djboiler"),
                },
            }
            
            # Validate using Pydantic
            EnvironmentConfig(**config_data)
            
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                self.errors.append(f"Configuration error in {field}: {error['msg']}")
        except ValueError as e:
            self.errors.append(f"Configuration validation error: {str(e)}")
    
    def _validate_security_settings(self):
        """Validate security-related settings."""
        # Check for insecure defaults
        secret_key = os.getenv("SECRET_KEY", "")
        if "django-insecure" in secret_key:
            self.errors.append("Secret key contains 'django-insecure' - change to secure key")
        
        # Password complexity for production
        if self.django_env == "production":
            postgres_password = os.getenv("POSTGRES_PASSWORD", "")
            if len(postgres_password) < 12:
                self.warnings.append("Consider using longer password for production database")
        
        # SSL/TLS checks
        if self.django_env in ["production", "staging"]:
            if not os.getenv("EMAIL_USE_TLS", "false").lower() == "true":
                self.warnings.append("Consider enabling EMAIL_USE_TLS for secure email delivery")
    
    def print_validation_results(self, results: Dict):
        """
        Print validation results in a formatted way.
        
        Args:
            results: Validation results from validate_all()
        """
        print(f"\n{style.HTTP_INFO}Environment Validation Results{style.ENDC}")
        print(f"Environment: {style.HTTP_SUCCESS if results['success'] else style.ERROR}{results['environment']}{style.ENDC}")
        print(f"Status: {style.HTTP_SUCCESS if results['success'] else style.ERROR}{'✓ PASS' if results['success'] else '✗ FAIL'}{style.ENDC}")
        
        if results["errors"]:
            print(f"\n{style.ERROR}Errors ({len(results['errors'])})::{style.ENDC}")
            for error in results["errors"]:
                print(f"  {style.ERROR}✗{style.ENDC} {error}")
        
        if results["warnings"]:
            print(f"\n{style.WARNING}Warnings ({len(results['warnings'])})::{style.ENDC}")
            for warning in results["warnings"]:
                print(f"  {style.WARNING}!{style.ENDC} {warning}")
        
        if results["success"] and not results["warnings"]:
            print(f"\n{style.HTTP_SUCCESS}All environment validation checks passed!{style.ENDC}")
        
        print()  # Empty line at the end


def validate_environment() -> bool:
    """
    Quick environment validation function.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    validator = EnvironmentValidator()
    results = validator.validate_all()
    
    if not results["success"]:
        logger.error("Environment validation failed", 
                    errors=results["errors"],
                    warnings=results["warnings"])
        return False
    
    if results["warnings"]:
        logger.warning("Environment validation passed with warnings",
                      warnings=results["warnings"])
    else:
        logger.info("Environment validation passed successfully")
    
    return True


def validate_environment_or_exit() -> None:
    """
    Validate environment and exit if validation fails.
    
    This function should be called during application startup to ensure
    proper configuration before the application starts.
    """
    validator = EnvironmentValidator()
    results = validator.validate_all()
    
    # Always print results for visibility
    validator.print_validation_results(results)
    
    if not results["success"]:
        print(f"{style.ERROR}Environment validation failed. Please fix the errors above.{style.ENDC}")
        sys.exit(1)
    
    if results["warnings"]:
        print(f"{style.WARNING}Environment validation passed with warnings. Consider addressing them.{style.ENDC}")


# Utility function to get environment info
def get_environment_info() -> Dict[str, Union[str, bool, List[str]]]:
    """
    Get current environment information.
    
    Returns:
        dict: Environment information including Django settings
    """
    return {
        "django_env": os.getenv("DJANGO_ENV", "unknown"),
        "debug_mode": getattr(settings, "DEBUG", False),
        "database_engine": getattr(settings, "DATABASES", {}).get("default", {}).get("ENGINE", "unknown"),
        "cache_backend": getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", "unknown"),
        "allowed_hosts": getattr(settings, "ALLOWED_HOSTS", []),
        "installed_apps_count": len(getattr(settings, "INSTALLED_APPS", [])),
        "middleware_count": len(getattr(settings, "MIDDLEWARE", [])),
        "time_zone": getattr(settings, "TIME_ZONE", "unknown"),
        "language_code": getattr(settings, "LANGUAGE_CODE", "unknown"),
        "use_postgres": os.getenv("USE_POSTGRES", "false").lower() == "true",
        "use_redis_cache": os.getenv("USE_REDIS_CACHE", "false").lower() == "true",
    }