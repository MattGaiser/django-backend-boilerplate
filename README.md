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

### Environment Setup

Each environment has its own configuration:

#### Development Environment

Includes pgAdmin for database inspection.

```bash
# Copy environment file
cp .env.dev .env

# Start all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or in detached mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Services available:
- Django: http://localhost:8000
- Prefect UI: http://localhost:4200
- pgAdmin: http://localhost:5050 (admin@admin.com / admin)

#### Test Environment

Uses ephemeral volumes and runs tests.

```bash
# Copy environment file
cp .env.test .env

# Run tests
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit

# Clean up
docker-compose -f docker-compose.yml -f docker-compose.test.yml down -v
```

#### Staging Environment

Production-like setup with restart policies.

```bash
# Copy and configure environment file
cp .env.staging .env
# Edit .env to update SECRET_KEY, POSTGRES_PASSWORD, and ALLOWED_HOSTS

# Start services
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

#### Production Environment

Optimized for production with multiple Gunicorn workers and minimal Prefect UI.

```bash
# Copy and configure environment file
cp .env.production .env
# Edit .env to update SECRET_KEY, POSTGRES_PASSWORD, and ALLOWED_HOSTS

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
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
docker-compose logs -f django

# Execute Django management commands
docker-compose exec django python manage.py makemigrations
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py createsuperuser

# Access Django shell
docker-compose exec django python manage.py shell

# Access database
docker-compose exec db psql -U django_dev_user -d django_dev_db

# Stop all services
docker-compose down

# Remove volumes (careful!)
docker-compose down -v
```

### Working with Prefect

```bash
# Access Prefect CLI
docker-compose exec prefect-agent prefect --help

# Create a new work pool
docker-compose exec prefect-agent prefect work-pool create my-pool

# Deploy a flow (from Django app)
docker-compose exec django python manage.py shell
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
docker-compose ps

# View all logs
docker-compose logs

# View specific service logs
docker-compose logs django
docker-compose logs db
docker-compose logs prefect-server

# Follow logs in real-time
docker-compose logs -f
```

## Contributing

1. Make changes in your development environment
2. Test with the test environment setup
3. Verify in staging before production deployment

## License

This project is licensed under the MIT License.