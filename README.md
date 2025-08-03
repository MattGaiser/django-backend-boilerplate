# Django Backend Boilerplate

An enterprise-ready Django backend boilerplate with comprehensive multi-tenant architecture, role-based access control (RBAC), and production-grade features. Includes one-click Docker Compose setup for all environments.

## Features

### 🏗️ Enterprise Architecture
- **Custom User Model**: Email-based authentication with UUID primary keys
- **Multi-Tenancy**: Organization-based data isolation with role-based permissions  
- **RBAC System**: Admin, Manager, and Viewer roles with organization scoping
- **SSO Integration**: Google OAuth2 and Azure AD via django-allauth
- **Audit Trails**: Automatic tracking of created_by, updated_by, and timestamps
- **Soft Delete**: Safe data removal with recovery capabilities
- **PII Compliance**: Built-in PII field tracking and data protection

### 🚀 API Framework
- **Django REST Framework**: Token authentication with secure defaults
- **API Versioning**: URL path versioning (`/api/v1/`) ready for evolution
- **Comprehensive Permissions**: Organization-scoped access control
- **Structured Responses**: Consistent error handling and pagination
- **OpenAPI Ready**: Documented endpoints with translation support

### 🌐 Internationalization & Localization
- **Multi-Language Support**: English and French with easy extensibility
- **User Preferences**: Per-user and per-organization language settings
- **Translation Workflow**: Management commands for translation updates
- **Timezone Support**: User-specific timezone handling

### 🧪 Development & Testing
- **Pytest Framework**: Comprehensive test suite with factories
- **Factory Boy**: Test data generation with realistic fixtures
- **Demo Data**: Automated demo user and organization creation
- **Structured Logging**: JSON logging with request tracking

### 🐳 Infrastructure
- **Docker Compose**: Multi-environment setup (dev, test, staging, production)
- **PostgreSQL**: Production-ready database with health checks
- **Prefect Integration**: Workflow orchestration and task management
- **Environment Isolation**: Separate configurations for each deployment stage
- **pgAdmin**: Database administration interface (development)

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### One-Command Bootstrap (Development)

For the fastest onboarding experience, use the cleanup script that automatically sets up everything:

```bash
# Complete setup with demo data (recommended for new developers)
./docker-cleanup.sh dev
```

This will:
1. 🧹 Clean up any existing containers/networks/images
2. 🐳 Start all Docker services (PostgreSQL, Prefect, Django)
3. 📊 Apply database migrations
4. 🌱 Seed demo data (users, organizations)
5. 🚀 Start the development server

After completion, you'll see demo credentials output to the terminal for immediate access.

### Manual Development Setup

If you prefer manual control or are troubleshooting:

#### Development Environment

Includes pgAdmin for database inspection and hot-reload capabilities.

```bash
# Start all services (automatically loads .env.dev)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or in detached mode
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Services available:
- Django: http://localhost:8001 (note: port 8001 for dev environment)
- Prefect UI: http://localhost:4200
- pgAdmin: http://localhost:5050 (admin@admin.com / admin)

### Demo Data and Credentials

The development environment automatically creates demo data for immediate use:

**🔑 Demo Credentials:**
- **Super Admin**: admin@demo.com / admin123 (Django admin access)
- **Editor**: user@demo.com / user123 (API access only)  
- **Viewer**: viewer@demo.com / viewer123 (API access only)

**📍 Access URLs:**
- Django Admin: http://localhost:8001/admin/
- API Root: http://localhost:8001/
- Prefect UI: http://localhost:4200/
- pgAdmin: http://localhost:5050/

**🌱 Manual Demo Data Management:**
```bash
# Seed demo data manually
docker compose exec django python manage.py seed_demo_data

# Reset and reseed demo data
docker compose exec django python manage.py seed_demo_data --clean
```

#### Test Environment

Uses ephemeral volumes and runs automated tests.

```bash
# Run tests (automatically loads .env.test)
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit

# Clean up
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v
```

#### Staging Environment

Production-like setup with restart policies and persistent storage.

```bash
# IMPORTANT: Update staging secrets before deploying
# Edit .env.staging to update SECRET_KEY, POSTGRES_PASSWORD, and ALLOWED_HOSTS

# Start services (automatically loads .env.staging)
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

#### Production Environment

Optimized for production with multiple Gunicorn workers and minimal Prefect UI.

```bash
# IMPORTANT: Update production secrets before deploying
# Edit .env.production to update SECRET_KEY, POSTGRES_PASSWORD, and ALLOWED_HOSTS

# Start services (automatically loads .env.production)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## SSO Integration

This boilerplate includes comprehensive SSO (Single Sign-On) integration via django-allauth, supporting both social authentication and email-based login.

### Features

- ✅ **Email-based authentication** as default (username login disabled)
- ✅ **Google OAuth2** and **Azure AD** social providers pre-configured
- ✅ **Django Admin integration** for managing social applications
- ✅ **Custom adapters** for organization scoping during login
- ✅ **Environment-based credentials** for secure configuration
- ✅ **Development-friendly** with mock credentials support

### Authentication Endpoints

All authentication endpoints are available under `/accounts/`:

- **Login**: `/accounts/login/`
- **Signup**: `/accounts/signup/`
- **Logout**: `/accounts/logout/`
- **Password Reset**: `/accounts/password/reset/`
- **Social Login**: `/accounts/google/login/` and `/accounts/microsoft/login/`

### Google OAuth2 Setup

#### 1. Create Google OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Configure OAuth consent screen with your domain
6. Add authorized redirect URIs:
   - `http://localhost:8001/accounts/google/login/callback/` (development)
   - `https://yourdomain.com/accounts/google/login/callback/` (production)

#### 2. Configure Environment Variables

Add your Google OAuth2 credentials to your environment files:

**Development (`.env.dev`):**
```bash
# Google OAuth2 - Replace with actual credentials
GOOGLE_OAUTH2_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-your-actual-client-secret
```

**Production (`.env.production`):**
```bash
# Google OAuth2 - Production credentials
GOOGLE_OAUTH2_CLIENT_ID=your-production-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-your-production-client-secret
```

#### 3. Create Social Application in Django Admin

1. Start your Django server
2. Go to Django Admin: `http://localhost:8001/admin/`
3. Navigate to **Social Applications** → **Add**
4. Configure:
   - **Provider**: Google
   - **Name**: Google OAuth2
   - **Client ID**: Your Google client ID
   - **Secret Key**: Your Google client secret
   - **Sites**: Select your site (usually `example.com`)

### Azure AD Setup

#### 1. Register Application in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure:
   - **Name**: Your app name
   - **Supported account types**: Choose appropriate option
   - **Redirect URI**: Web → `http://localhost:8001/accounts/microsoft/login/callback/`

#### 2. Configure App Registration

1. Note the **Application (client) ID**
2. Go to **Certificates & secrets** → **New client secret**
3. Note the **client secret value** (copy immediately!)
4. Go to **API permissions** → **Add a permission**
5. Add Microsoft Graph permissions: `User.Read`, `email`, `profile`

#### 3. Configure Environment Variables

**Development (`.env.dev`):**
```bash
# Azure AD / Microsoft - Replace with actual credentials
AZURE_AD_CLIENT_ID=your-azure-ad-application-client-id
AZURE_AD_CLIENT_SECRET=your-azure-ad-client-secret
```

**Production (`.env.production`):**
```bash
# Azure AD / Microsoft - Production credentials
AZURE_AD_CLIENT_ID=your-production-azure-ad-client-id
AZURE_AD_CLIENT_SECRET=your-production-azure-ad-client-secret
```

#### 4. Create Social Application in Django Admin

1. Navigate to **Social Applications** → **Add**
2. Configure:
   - **Provider**: Microsoft
   - **Name**: Azure AD
   - **Client ID**: Your Azure AD client ID
   - **Secret Key**: Your Azure AD client secret
   - **Sites**: Select your site

### Local Development with Mock Credentials

For local development, the boilerplate includes mock/placeholder credentials that won't work for actual authentication but allow the application to start without errors:

```bash
# These are in .env.dev and .env.test by default
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-your-google-client-secret

AZURE_AD_CLIENT_ID=your-azure-ad-application-client-id
AZURE_AD_CLIENT_SECRET=your-azure-ad-client-secret
```

### Testing SSO Integration

The boilerplate includes comprehensive tests for SSO functionality:

```bash
# Run all SSO tests
docker compose exec django python -m pytest core/tests/test_sso_integration.py -v

# Run specific SSO test categories
docker compose exec django python -m pytest core/tests/test_sso_integration.py::TestAllauthConfiguration -v
docker compose exec django python -m pytest core/tests/test_sso_integration.py::TestCustomAdapters -v
```

### Customizing SSO Behavior

#### Custom Social Account Adapter

The boilerplate includes a custom `CustomSocialAccountAdapter` in `core/adapters.py` that provides:

- **Email-based user matching**: Automatically connects social accounts to existing users with matching emails
- **Custom user data extraction**: Pulls name, locale, and other data from social providers
- **Organization scoping placeholder**: Ready for implementing organization assignment logic
- **Error handling**: User-friendly error messages for authentication failures

#### Organization Assignment

The current implementation includes a placeholder for organization assignment during SSO login. You can customize the `_handle_organization_assignment` method in `core/adapters.py` to:

- Assign users to organizations based on email domain
- Check for pending invitations
- Create default personal organizations
- Implement custom business rules

### Troubleshooting

#### Common Issues

1. **OAuth callback errors**: Ensure redirect URIs in your provider match exactly
2. **Missing client ID/secret**: Check environment variables are loaded correctly
3. **Site framework errors**: Ensure `SITE_ID = 1` is set and Site exists in database
4. **Email verification issues**: Check email backend configuration for production

#### Debug Social Authentication

Enable verbose logging for social authentication:

```python
# In settings.py
LOGGING['loggers']['allauth'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
}
```

#### Test Social App Configuration

```bash
# Check if social apps are configured correctly
docker compose exec django python manage.py shell
>>> from allauth.socialaccount.models import SocialApp
>>> SocialApp.objects.all()
>>> # Should show your configured social applications
```


## Architecture

### Core Models & Systems

#### BaseModel Foundation
All models inherit from `BaseModel` providing:
- **UUID Primary Keys**: Scalable and secure identifiers
- **Audit Fields**: Automatic `created_at`, `updated_at`, `created_by`, `updated_by`
- **Soft Delete**: `deleted_at` field with custom managers
- **PII Compliance**: Mandatory declaration of personally identifiable fields

#### User & Organization System  
- **Custom User Model**: Email-based authentication, timezone/language preferences
- **Organization Model**: Multi-tenant isolation with subscription plans
- **OrganizationMembership**: Through model managing user roles within organizations
- **Role Hierarchy**: Admin (full access) → Manager (most features) → Viewer (read-only)

#### API Framework
- **Token Authentication**: Secure stateless authentication
- **Organization Scoping**: All data automatically scoped to user's organizations  
- **Permission Classes**: Custom DRF permissions for role-based access
- **Versioned Endpoints**: `/api/v1/` with planned evolution path

### Infrastructure Services

1. **Django Application**
   - Runs on port 8000 (8001 in development)
   - Custom User model with email authentication
   - Structured logging with request tracking
   - Uses Gunicorn in staging/production

2. **PostgreSQL Database**
   - Persistent volumes for dev/staging/production
   - Ephemeral storage for testing
   - Health checks for reliable startup
   - Supports both Django and Prefect databases

3. **Prefect Server**
   - Workflow orchestration server
   - Web UI available on port 4200 (except production)
   - Uses PostgreSQL for metadata storage

4. **Prefect Agent**
   - Executes workflows
   - Docker-enabled for running containerized flows
   - Connects to default work pool

5. **pgAdmin** (Development only)
   - Database administration interface
   - Available on port 5050

### Environment Configuration

| Environment | Debug | Database | Prefect UI | Volumes | Restart Policy |
|-------------|-------|----------|------------|---------|----------------|
| Development | ✅ | Persistent | ✅ | Named | None |
| Test | ❌ | Ephemeral | ❌ | Tmpfs | None |
| Staging | ❌ | Persistent | ✅ | Named | unless-stopped |
| Production | ❌ | Persistent | ❌ | Named | unless-stopped |

## Configuration

### Environment Variables

Key environment variables in `.env` files:

```bash
# Django
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
POSTGRES_DB=django_db
POSTGRES_USER=django_user
POSTGRES_PASSWORD=your-password

# Prefect
PREFECT_API_URL=http://prefect-server:4200/api
```

### Security Notes

**Important**: Before deploying to staging or production:

1. Change `SECRET_KEY` to a secure random string
2. Update `POSTGRES_PASSWORD` to a strong password
3. Configure `ALLOWED_HOSTS` with your actual domain names
4. Consider using Docker secrets or external secret management

## Development Workflow

### Testing Framework

The project uses a comprehensive testing setup with pytest:

```bash
# Run all tests in containerized environment
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit

# Run tests locally (requires dependencies)
pytest -v

# Run specific test modules
pytest core/tests/ -v
pytest api/v1/tests/ -v

# Run with coverage
pytest --cov=core --cov=api -v
```

### Demo Data and Development

Create demo data for immediate development:

```bash
# Seed demo data (creates users, organizations, memberships)
docker compose exec django python manage.py seed_demo_data

# Reset and reseed demo data
docker compose exec django python manage.py seed_demo_data --clean

# Create custom users programmatically
docker compose exec django python manage.py shell
>>> from core.factories import UserFactory, OrganizationFactory
>>> user = UserFactory()
>>> org = OrganizationFactory()
```

### Common Commands

```bash
# View logs
docker compose logs -f django

# Execute Django management commands
docker compose exec django python manage.py makemigrations
docker compose exec django python manage.py migrate
docker compose exec django python manage.py createsuperuser

# Seed demo data (users, organizations)
docker compose exec django python manage.py seed_demo_data

# Reset demo data
docker compose exec django python manage.py seed_demo_data --clean

# Access Django shell
docker compose exec django python manage.py shell

# Access database
docker compose exec db psql -U django_dev_user -d django_dev_db

# Stop all services
docker compose down

# Remove volumes (careful!)
docker compose down -v

# Quick restart with fresh build
./docker-cleanup.sh dev
```

### Working with Prefect

```bash
# Access Prefect CLI
docker compose exec prefect-agent prefect --help

# Create a new work pool
docker compose exec prefect-agent prefect work-pool create my-pool

# Deploy a flow (from Django app)
docker compose exec django python manage.py shell
>>> import prefect
>>> # Your Prefect flow code here
```

### API Development

The boilerplate provides a production-ready API framework:

```bash
# Get authentication token
curl -X POST http://localhost:8001/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo.com", "password": "admin123"}'

# Use token for authenticated requests
curl -H "Authorization: Token your_token_here" \
  http://localhost:8001/api/v1/users/me/

# Test organization-scoped endpoints
curl -H "Authorization: Token your_token_here" \
  http://localhost:8001/api/v1/organizations/
```

See [API_README.md](API_README.md) for complete API documentation with examples.

### Working with Organizations & RBAC

```python
# Example: Creating organization memberships
from core.models import User, Organization, OrganizationMembership
from constants.roles import OrgRole

# Get user and organization
user = User.objects.get(email='user@demo.com')
org = Organization.objects.get(name='Demo Organization')

# Check user's role
role = user.get_role(org)
is_admin = user.has_role(org, OrgRole.ADMIN)

# Create new membership
OrganizationMembership.objects.create(
    user=user,
    organization=org, 
    role=OrgRole.MANAGER,
    is_default=True
)
```

See [RBAC_USAGE.md](RBAC_USAGE.md) for detailed role-based access control examples.

## Documentation

This boilerplate includes comprehensive documentation for each major system:

- **[API_README.md](API_README.md)** - Complete API documentation with authentication, endpoints, and examples
- **[CORE_MODELS_README.md](CORE_MODELS_README.md)** - BaseModel, Custom User, and core architecture
- **[RBAC_USAGE.md](RBAC_USAGE.md)** - Role-based access control implementation guide  
- **[TRANSLATIONS.md](TRANSLATIONS.md)** - Internationalization workflow and translation management
- **[CHANGELOG.md](CHANGELOG.md)** - Project changelog following semantic versioning

## Project Structure

```
.
├── core/                       # Core models and business logic
│   ├── models.py              # BaseModel, User, Organization, OrganizationMembership
│   ├── admin.py               # Django admin configuration
│   ├── factories.py           # Test data factories
│   ├── middleware.py          # Custom middleware (user tracking, logging)
│   ├── mixins.py              # Reusable model and view mixins
│   └── management/commands/   # Custom management commands
├── api/                        # REST API implementation
│   └── v1/                    # API version 1
│       ├── views/             # API viewsets and endpoints
│       ├── serializers/       # DRF serializers
│       ├── permissions.py     # Custom permission classes
│       └── tests/             # API test suite
├── constants/                  # Application constants and enums
│   └── roles.py               # RBAC role definitions
├── locale/                     # Translation files
│   └── fr/LC_MESSAGES/        # French translations
├── DjangoBoilerplate/          # Django project settings
│   ├── settings.py            # Environment-aware configuration
│   ├── urls.py                # URL routing
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
├── docker-compose.yml         # Base Docker services
├── docker-compose.dev.yml     # Development overrides
├── docker-compose.test.yml    # Test environment
├── docker-compose.staging.yml # Staging environment  
├── docker-compose.prod.yml    # Production environment
├── Dockerfile                 # Django application container
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── pytest.ini                # Pytest configuration
├── conftest.py                # Shared test fixtures
├── .env.dev                   # Development environment variables
├── .env.test                  # Test environment variables
├── .env.staging               # Staging environment variables
├── .env.production            # Production environment variables
└── manage.py                  # Django management script
```

## Enterprise Features

This boilerplate is designed for production use with enterprise-grade features:

### Security & Compliance
- **PII Data Protection**: Built-in personally identifiable information field tracking
- **Audit Trails**: Complete tracking of who created/modified each record and when
- **Secure Authentication**: Token-based authentication with organization scoping
- **Role-Based Permissions**: Granular access control with admin, manager, and viewer roles

### Scalability & Maintainability  
- **Multi-Tenant Architecture**: Organization-based data isolation supporting multiple clients
- **UUID Primary Keys**: Collision-resistant identifiers suitable for distributed systems
- **Soft Delete**: Safe data removal with ability to recover accidentally deleted records
- **Database Optimization**: Proper indexing on foreign keys and frequently queried fields

### Development Experience
- **Comprehensive Testing**: Factory-based test data generation with pytest framework
- **API Documentation**: Auto-generated documentation with examples and authentication
- **Translation Ready**: Built-in i18n support with management commands for translation updates
- **Structured Logging**: JSON-formatted logs with request tracking for observability

### Production Deployment
- **Environment Separation**: Distinct configurations for development, testing, staging, and production
- **Health Checks**: Database and service health monitoring for reliable deployments
- **Container Ready**: Optimized Docker images with proper user permissions and security
- **Workflow Integration**: Prefect orchestration for background tasks and data pipelines

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change port mappings in override files if needed
2. **Permission issues**: Ensure Docker has access to the project directory
3. **Database connection**: Verify PostgreSQL is healthy before Django starts
4. **Prefect connection**: Check that Prefect server is running and accessible

### Logs and Debugging

```bash
# Check service status
docker compose ps

# View all logs
docker compose logs

# View specific service logs
docker compose logs django
docker compose logs db
docker compose logs prefect-server

# Follow logs in real-time
docker compose logs -f
```

## Contributing

### Development Workflow

1. **Set up development environment**: Use `./docker-cleanup.sh dev` for one-click setup
2. **Make changes**: Modify code following the established patterns and architecture
3. **Add tests**: Write pytest tests using factories for any new functionality  
4. **Test changes**: Run `docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit`
5. **Verify in staging**: Test in staging environment before production deployment
6. **Update documentation**: Update relevant README files if adding new features

### Architecture Guidelines

- All models should inherit from `BaseModel` for consistency
- Declare any PII fields in the model's `pii_fields` attribute
- Use the RBAC system for access control rather than custom permissions
- Follow the organization-scoped pattern for multi-tenant data access
- Add translation strings using `gettext_lazy` for user-facing content

### Testing Standards

- Use factory_boy factories for creating test data
- Write both unit and integration tests for new API endpoints
- Test RBAC permissions for any organization-scoped functionality
- Include edge cases and error conditions in test coverage

## License

This project is licensed under the MIT License.