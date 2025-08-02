# Django Backend Boilerplate with Docker Compose

A Django backend boilerplate with one-click Docker Compose setup for Development, Test, Staging, and Production environments. Includes Django + PostgreSQL + Prefect integration.

## Features

- 🐳 Docker Compose setup for all environments
- 🗄️ PostgreSQL database with environment-specific configurations
- ⚡ Prefect integration for workflow management
- 🔧 Environment-specific settings and overrides
- 📊 pgAdmin included in development environment
- 🚀 Production-ready with Gunicorn

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

## Architecture

### Services

1. **Django Application**
   - Runs on port 8000
   - Connects to PostgreSQL database
   - Includes Prefect client configuration
   - Uses Gunicorn in staging/production

2. **PostgreSQL Database**
   - Persistent volumes for dev/staging/production
   - Ephemeral storage for testing
   - Health checks for reliable startup

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

## Project Structure

```
.
├── DjangoBoilerplate/          # Django project
│   ├── settings.py            # Environment-aware settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── docker-compose.yml         # Base services
├── docker-compose.dev.yml     # Development overrides
├── docker-compose.test.yml    # Test overrides
├── docker-compose.staging.yml # Staging overrides
├── docker-compose.prod.yml    # Production overrides
├── Dockerfile                 # Django app container
├── requirements.txt           # Python dependencies
├── .env.dev                   # Development environment
├── .env.test                  # Test environment
├── .env.staging               # Staging environment
├── .env.production            # Production environment
└── manage.py                  # Django management script
```

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

1. Make changes in your development environment
2. Test with the test environment setup
3. Verify in staging before production deployment

## License

This project is licensed under the MIT License.