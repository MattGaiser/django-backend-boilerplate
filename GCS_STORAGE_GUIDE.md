# GCS Storage Integration with RBAC

This document explains how to use the Google Cloud Storage (GCS) integration with Role-Based Access Control (RBAC) in the Django backend.

## Overview

The GCS integration provides:
- Organization-scoped file storage
- Role-based access control for file operations
- Local development support with fake-gcs-server emulator
- Secure signed URL generation for file access
- Comprehensive API endpoints for file management

## Architecture

### Storage Backend
- `GCSStorage`: Base storage backend for GCS
- `OrganizationScopedGCSStorage`: RBAC-enforced storage with organization scoping
- All files are automatically prefixed with `orgs/{organization_id}/`

### Service Layer
- `StorageService`: High-level service with RBAC enforcement
- Validates user permissions before any operation
- Provides convenient methods for common file operations

### API Layer
- REST API endpoints under `/api/v1/storage/`
- Full CRUD operations with proper permission checks
- Support for file upload, download, listing, and management

## Development Setup

### Using the Emulator

The project includes a fake-gcs-server emulator for local development:

```bash
# Start the development environment
docker-compose up

# The emulator runs on http://localhost:9090
# Django automatically uses the emulator when USE_GCS_EMULATOR=true
```

### Environment Variables

```bash
# .env.dev (Local Development)
USE_GCS_EMULATOR=true
GCS_EMULATOR_HOST=http://fake-gcs-server:9090
GCS_BUCKET_NAME=dev-app-assets

# Production
USE_GCS_EMULATOR=false
GCS_BUCKET_NAME=prod-app-assets-[random-suffix]
```

## RBAC Permissions

### Role-Based Operations

| Operation | Admin | Manager | Viewer |
|-----------|-------|---------|--------|
| Upload files | ✅ | ✅ | ❌ |
| Download files | ✅ | ✅ | ✅ |
| Delete files | ✅ | ✅ | ❌ |
| List files | ✅ | ✅ | ✅ |
| View storage usage | ✅ | ✅ | ❌ |

### Organization Isolation

- All file operations are automatically scoped to the user's organization
- Users cannot access files from other organizations
- File paths are prefixed with `orgs/{organization_id}/`

## API Usage

### Upload a File

```bash
POST /api/v1/storage/upload/
Content-Type: multipart/form-data
Authorization: Token your-auth-token

# Form data:
# file: (binary file)
# category: "documents" (optional)
# file_path: "custom/path.txt" (optional)
# metadata: {"key": "value"} (optional JSON)
```

Response:
```json
{
  "message": "File uploaded successfully",
  "file": {
    "path": "orgs/org-id/documents/file.txt",
    "original_name": "document.txt",
    "size": 1024,
    "content_type": "text/plain",
    "category": "documents",
    "uploaded_by": "user-id",
    "organization": "org-id",
    "metadata": {},
    "url": "https://signed-url..."
  }
}
```

### Download a File

```bash
GET /api/v1/storage/download/documents/file.txt/?expire=3600
Authorization: Token your-auth-token
```

Response:
```json
{
  "download_url": "https://signed-url...",
  "file_path": "documents/file.txt",
  "expires_in_seconds": 3600
}
```

### List Files

```bash
GET /api/v1/storage/list/?directory=documents&category=images
Authorization: Token your-auth-token
```

Response:
```json
{
  "files": [
    {
      "name": "image.jpg",
      "path": "documents/image.jpg",
      "size": 2048,
      "modified_time": "2023-12-01T10:00:00Z",
      "url": "https://signed-url..."
    }
  ]
}
```

### Delete a File

```bash
DELETE /api/v1/storage/delete/documents/file.txt/
Authorization: Token your-auth-token
```

Response:
```json
{
  "message": "File deleted successfully"
}
```

### Get File Information

```bash
GET /api/v1/storage/info/documents/file.txt/
Authorization: Token your-auth-token
```

Response:
```json
{
  "path": "documents/file.txt",
  "size": 1024,
  "created_time": "2023-12-01T09:00:00Z",
  "modified_time": "2023-12-01T10:00:00Z",
  "exists": true,
  "url": "https://signed-url..."
}
```

### Get Storage Usage

```bash
GET /api/v1/storage/usage/
Authorization: Token your-auth-token
```

Response:
```json
{
  "total_size_bytes": 1048576,
  "total_size_mb": 1.0,
  "file_count": 10,
  "organization_id": "org-id",
  "organization_name": "My Organization"
}
```

## Programmatic Usage

### Using StorageService

```python
from core.services.storage import StorageService
from core.models import User, Organization

# Initialize service
user = User.objects.get(email="user@example.com")
organization = user.get_default_organization()
storage_service = StorageService(user=user, organization=organization)

# Upload a file
with open('document.pdf', 'rb') as f:
    from django.core.files.uploadedfile import SimpleUploadedFile
    uploaded_file = SimpleUploadedFile('document.pdf', f.read(), content_type='application/pdf')
    
    file_info = storage_service.upload_file(
        file=uploaded_file,
        category='documents',
        metadata={'department': 'HR'}
    )

# Get a signed URL
download_url = storage_service.get_file_url('documents/document.pdf', expire_seconds=1800)

# List files
files = storage_service.list_files(category='documents')

# Delete a file
storage_service.delete_file('documents/old-document.pdf')
```

### Using Storage Backend Directly

```python
from core.storage import OrganizationScopedGCSStorage

# Initialize storage (automatically scopes to current user's organization)
storage = OrganizationScopedGCSStorage()

# Save a file
from django.core.files.base import ContentFile
content = ContentFile(b'Hello, World!')
path = storage.save('hello.txt', content)

# Check if file exists
exists = storage.exists('hello.txt')

# Get file URL
url = storage.url('hello.txt')

# Delete file
storage.delete('hello.txt')
```

## File Categories

Supported file categories:
- `general` (default)
- `documents`
- `images`
- `videos`
- `audio`
- `archives`
- `spreadsheets`
- `presentations`
- `pdfs`

## Security Features

### File Validation
- File size limits (default: 50MB)
- Blocked dangerous file extensions (.exe, .bat, etc.)
- Path validation to prevent directory traversal

### Access Control
- All operations require authentication
- Organization membership validation
- Role-based permission checks
- Automatic organization scoping

### Signed URLs
- Temporary access URLs with configurable expiration
- No direct bucket access required
- Secure file sharing within organization

## Testing

### Unit Tests
```bash
# Run storage tests
python -m pytest core/tests/test_storage.py -v

# Run API tests
python -m pytest api/v1/tests/test_storage.py -v
```

### Manual Testing with Emulator
```bash
# Start development environment
docker-compose up

# Upload a test file
curl -X POST http://localhost:8000/api/v1/storage/upload/ \
  -H "Authorization: Token your-token" \
  -F "file=@test.txt" \
  -F "category=documents"

# Check emulator directly
curl http://localhost:9090/storage/v1/b/dev-app-assets/o
```

## Production Deployment

### Terraform Infrastructure
The cloud-storage module creates:
- GCS buckets for each environment (test, prod)
- IAM policies for service accounts
- Bucket lifecycle rules
- CORS configuration

### Service Account Permissions
Required GCS permissions:
- `roles/storage.objectAdmin` (for backend service account)
- `roles/storage.legacyBucketReader` (for bucket operations)

### Environment-Specific Settings
```bash
# Test Environment
GCS_BUCKET_NAME=test-app-assets-[suffix]
USE_GCS_EMULATOR=false

# Production Environment  
GCS_BUCKET_NAME=prod-app-assets-[suffix]
USE_GCS_EMULATOR=false
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check user's organization membership and role
2. **File Not Found**: Verify file path and organization scoping
3. **Upload Fails**: Check file size limits and content type validation
4. **Emulator Connection**: Ensure fake-gcs-server is running on port 9090

### Debug Logging
Enable debug logging for storage operations:
```python
import logging
logging.getLogger('core.storage').setLevel(logging.DEBUG)
logging.getLogger('core.services.storage').setLevel(logging.DEBUG)
```

## Configuration Options

### Storage Backend Settings
```python
# settings.py
USE_GCS_EMULATOR = config("USE_GCS_EMULATOR", default=False, cast=bool)
GCS_BUCKET_NAME = config("GCS_BUCKET_NAME", default="dev-app-assets")
GCS_EMULATOR_HOST = config("GCS_EMULATOR_HOST", default="http://fake-gcs-server:9090")
DEFAULT_FILE_STORAGE = "core.storage.GCSStorage"
MAX_FILE_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
```

### Terraform Variables
```hcl
# terraform/test/terraform.tfvars
project_id = "your-gcp-project"
region = "us-central1"
django_secret_key = "your-secret-key"
database_password = "your-db-password"
```

This integration provides a complete, secure, and scalable file storage solution with proper RBAC enforcement for multi-tenant applications.