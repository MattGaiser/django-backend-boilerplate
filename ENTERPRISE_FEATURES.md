# Enterprise Features Guide

This document describes the enhanced enterprise features added to the Django Backend Boilerplate to make it production-ready for enterprise applications.

## 🚀 New Enterprise Features

### 1. API Documentation (OpenAPI/Swagger)

**What it provides:**
- Auto-generated API documentation from code
- Interactive API explorer with authentication
- OpenAPI 3.0 schema generation
- Multiple documentation formats (Swagger UI, ReDoc)

**Endpoints:**
- `/api/docs/` - Swagger UI documentation
- `/api/redoc/` - ReDoc documentation  
- `/api/schema/` - Raw OpenAPI schema

**Configuration:**
```python
# In settings.py
SPECTACULAR_SETTINGS = {
    "TITLE": "Django Backend Boilerplate API",
    "DESCRIPTION": "Enterprise-ready Django backend...",
    "VERSION": "1.0.0",
    # ... additional settings
}
```

**Usage:**
```python
# Add schema documentation to views
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema(
    description="Get user profile information",
    responses={200: UserSerializer},
    tags=["Users"]
)
def get_user_profile(request):
    pass
```

### 2. Enhanced Monitoring & Metrics

**What it provides:**
- Prometheus-compatible metrics endpoint
- Custom application metrics
- System health monitoring
- Performance tracking
- Database and cache monitoring

**Endpoints:**
- `/api/v1/metrics/` - JSON application metrics
- `/api/v1/metrics/prometheus/` - Prometheus format metrics
- `/api/v1/system/status/` - Detailed system status
- `/metrics/` - Django-prometheus system metrics
- `/api/v1/health/live/` - Kubernetes liveness probe
- `/api/v1/health/ready/` - Kubernetes readiness probe

**Custom Metrics Available:**
- User counts by role
- Organization metrics
- Cache performance
- Database connection status
- Request latency
- Custom business metrics

**Example Integration:**
```python
# Monitor custom business logic
from api.v1.views.metrics import MetricsView

# Metrics are automatically collected from:
# - User models
# - Organization models  
# - Cache operations
# - Database queries
```

### 3. Caching Layer with Redis

**What it provides:**
- Redis cache backend with connection pooling
- Cache decorators for functions and views
- Organization-scoped cache keys
- Cache invalidation patterns
- Performance monitoring

**Configuration:**
```bash
# In .env
USE_REDIS_CACHE=true
REDIS_URL=redis://redis:6379/1
CACHE_KEY_PREFIX=djboiler
```

**Usage Examples:**
```python
from core.cache import cache_result, cache_key_for_org, invalidate_org_cache

# Cache function results
@cache_result(timeout=300)
def expensive_calculation(param1, param2):
    return complex_operation()

# Organization-scoped caching
cache_key = cache_key_for_org(org.id, "user_stats")
cache.set(cache_key, user_stats, timeout=600)

# Invalidate organization cache
invalidate_org_cache(organization.id)
```

### 4. Pre-commit Hooks & Code Quality

**What it provides:**
- Automated code formatting (Black, isort)
- Static analysis (flake8, mypy, bandit)
- Security scanning (detect-secrets)
- Django-specific checks
- Conventional commit format enforcement

**Setup:**
```bash
# Install and configure
./setup-development.sh

# Or manually
pre-commit install
pre-commit run --all-files
```

**Hooks Include:**
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **bandit** - Security analysis
- **detect-secrets** - Secrets detection
- **autoflake** - Remove unused imports

### 5. Environment Validation

**What it provides:**
- Comprehensive environment variable validation
- Environment-specific requirement checking
- Security settings validation
- Configuration error detection

**Usage:**
```bash
# Validate current environment
python manage.py validate_environment

# Exit with error if validation fails
python manage.py validate_environment --exit-on-fail

# JSON output for automation
python manage.py validate_environment --json
```

**Validation Includes:**
- Required environment variables
- Password complexity (production)
- SSL/security settings
- Database configuration
- SSO configuration
- Cache settings

### 6. Webhook System

**What it provides:**
- Flexible webhook framework
- Event-driven notifications
- HMAC signature verification
- Retry logic with exponential backoff
- Organization-scoped events

**Configuration:**
```python
# In settings.py
WEBHOOKS = {
    "ENABLED": True,
    "TIMEOUT": 30,
    "RETRY_ATTEMPTS": 3,
    "EVENTS": [
        "user.created",
        "user.updated",
        "organization.created",
        "organization.updated",
    ],
}

NOTIFICATIONS = {
    "WEBHOOK_ENDPOINTS": [
        "https://your-service.com/webhooks",
        "https://another-service.com/api/webhook",
    ],
}
```

**Usage:**
```python
from core.webhooks import send_user_webhook, send_organization_webhook

# Send user event
send_user_webhook("user.created", user, {"source": "api"})

# Send organization event  
send_organization_webhook("organization.updated", org, {"changes": ["name", "plan"]})
```

### 7. Enhanced Health Checks

**What it provides:**
- Comprehensive health monitoring
- Database connectivity checks
- Cache functionality tests
- External dependency verification
- Kubernetes-compatible probes

**Endpoints:**
- `/api/v1/health/` - Comprehensive health check
- `/api/v1/health/live/` - Liveness probe (basic)
- `/api/v1/health/ready/` - Readiness probe (with dependencies)

**Health Check Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "environment": "production",
  "checks": {
    "database": {"status": "healthy", "response_time_ms": 12.5},
    "cache": {"status": "healthy", "response_time_ms": 3.2},
    "django": {"status": "healthy", "user_count": 1250},
    "storage": {"status": "healthy", "backend": "GCSStorage"}
  },
  "metrics": {
    "response_time_ms": 45.8,
    "python_version": "3.11.0",
    "process_id": 1234
  }
}
```

### 8. Performance Profiling (Development)

**What it provides:**
- Django Silk for request profiling
- SQL query analysis
- Performance bottleneck identification
- Memory usage tracking

**Access:**
- `/silk/` - Profiling dashboard (development only)

**Features:**
- Request timing analysis
- Database query profiling
- Python code profiling
- Memory usage tracking

### 9. Enhanced Security Features

**What it provides:**
- Rate limiting with django-ratelimit
- Enhanced security headers
- File upload security
- Input validation
- Secrets management

**Security Headers Added:**
- Content Security Policy (CSP)
- Cross-Origin Opener Policy
- Permissions Policy
- Referrer Policy

**File Upload Security:**
- Extension whitelist/blacklist
- File size limits
- MIME type validation
- Safe file permissions

### 10. Background Jobs Enhancement

**What it provides:**
- Enhanced job configuration
- Retry logic
- Job monitoring
- Queue management

**Configuration:**
```python
BACKGROUND_JOBS = {
    "ENABLED": True,
    "QUEUE_NAME": "default",
    "RETRY_ATTEMPTS": 3,
    "TIMEOUT": 300,
}
```

## 🛠️ Development Workflow Improvements

### One-Command Setup

```bash
# Complete development environment setup
./setup-development.sh
```

This script:
1. Sets up Python virtual environment
2. Installs all dependencies
3. Configures pre-commit hooks
4. Sets up mypy type checking
5. Creates development .env file
6. Validates environment configuration

### Enhanced Testing

```bash
# Run with coverage and performance metrics
pytest --cov=core --cov=api -v --tb=short

# Run specific test categories
pytest core/tests/test_cache.py -v
pytest api/v1/tests/test_metrics.py -v
```

### Code Quality Commands

```bash
# Run all code quality checks
pre-commit run --all-files

# Individual tools
black . --check
isort . --check-only
flake8
mypy .
bandit -r . -f json
```

## 🔧 Configuration Examples

### Production Environment Variables

```bash
# Security
SECRET_KEY=your-secure-secret-key-here
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database
USE_POSTGRES=true
POSTGRES_DB=production_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure-password-here
POSTGRES_HOST=db.example.com

# Cache
USE_REDIS_CACHE=true
REDIS_URL=redis://redis.example.com:6379/1

# Monitoring
PROMETHEUS_EXPORT_MIGRATIONS=false

# Background Jobs
BACKGROUND_JOBS_ENABLED=true
JOB_RETRY_ATTEMPTS=3

# Webhooks
WEBHOOKS_ENABLED=true
WEBHOOK_TIMEOUT=30
```

### Docker Compose Integration

The enhanced features work seamlessly with the existing Docker setup:

```yaml
# docker-compose.prod.yml additions
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  django:
    environment:
      - USE_REDIS_CACHE=true
      - REDIS_URL=redis://redis:6379/1
      - WEBHOOKS_ENABLED=true
```

## 📊 Monitoring & Observability

### Prometheus Integration

1. **Automatic Metrics**: Django-prometheus provides request metrics, database metrics, and cache metrics
2. **Custom Metrics**: Application-specific metrics via `/api/v1/metrics/prometheus/`
3. **Alerting**: Configure alerts based on health check failures or performance degradation

### Grafana Dashboard

Example metrics to monitor:
- Request latency (95th percentile)
- Error rates by endpoint
- Database connection pool usage
- Cache hit rates
- User registration rates
- Organization growth metrics

### Log Aggregation

Enhanced structured logging includes:
- Request IDs for tracing
- User and organization context
- Performance metrics
- Error details with stack traces
- Security events

## 🔒 Security Enhancements

### Rate Limiting

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/h', method='POST')
def api_endpoint(request):
    pass
```

### Input Validation

```python
from core.validation import validate_environment

# Environment validation at startup
validate_environment_or_exit()
```

### File Upload Security

```python
ALLOWED_FILE_EXTENSIONS = ['.jpg', '.png', '.pdf', '.docx']
DANGEROUS_FILE_EXTENSIONS = ['.exe', '.bat', '.js', '.php']
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
```

## 🚀 Deployment Considerations

### Kubernetes Deployment

The enhanced health checks support Kubernetes deployment patterns:

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: django
        livenessProbe:
          httpGet:
            path: /api/v1/health/live/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Production Checklist

- [ ] Update all environment variables
- [ ] Configure Redis cache
- [ ] Set up Prometheus monitoring
- [ ] Configure webhook endpoints
- [ ] Enable rate limiting
- [ ] Set up log aggregation
- [ ] Configure backup procedures
- [ ] Set up alerting rules
- [ ] Review security headers
- [ ] Test health check endpoints

## 📚 Additional Resources

- **API Documentation**: `/api/docs/` - Interactive API explorer
- **System Status**: `/api/v1/system/status/` - Detailed system information
- **Metrics**: `/api/v1/metrics/` - Application metrics
- **Health Checks**: `/api/v1/health/` - Service health status

These enterprise features transform the Django Backend Boilerplate into a production-ready, enterprise-grade backend system with comprehensive monitoring, security, and developer experience improvements.