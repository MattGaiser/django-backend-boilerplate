# GitHub Actions CI/CD Setup Documentation

This document outlines the GitHub Secrets and configuration needed for the CI/CD pipeline.

## Required GitHub Secrets

The following secrets must be configured in your GitHub repository settings:

### GCP Authentication
- **`GCP_CREDENTIALS`**: Base64-encoded JSON service account key with the following roles:
  - `roles/editor` (or more specific roles)
  - `roles/cloudsql.admin`
  - `roles/run.admin`
  - `roles/storage.admin`
  - `roles/artifactregistry.admin`
  - `roles/secretmanager.admin`

### GCP Project Configuration
- **`GCP_PROJECT_ID`**: Your Google Cloud Project ID

### Test Environment Secrets
- **`DJANGO_SECRET_KEY_TEST`**: Django secret key for test environment
- **`DB_PASSWORD_TEST`**: Database password for test environment
- **`GOOGLE_OAUTH2_CLIENT_ID_TEST`**: Google OAuth2 Client ID for test environment
- **`GOOGLE_OAUTH2_CLIENT_SECRET_TEST`**: Google OAuth2 Client Secret for test environment
- **`AZURE_AD_CLIENT_ID_TEST`**: Azure AD (Microsoft) Client ID for test environment
- **`AZURE_AD_CLIENT_SECRET_TEST`**: Azure AD (Microsoft) Client Secret for test environment

### Production Environment Secrets  
- **`DJANGO_SECRET_KEY_PROD`**: Django secret key for production environment
- **`DB_PASSWORD_PROD`**: Database password for production environment
- **`GOOGLE_OAUTH2_CLIENT_ID_PROD`**: Google OAuth2 Client ID for production environment
- **`GOOGLE_OAUTH2_CLIENT_SECRET_PROD`**: Google OAuth2 Client Secret for production environment
- **`AZURE_AD_CLIENT_ID_PROD`**: Azure AD (Microsoft) Client ID for production environment
- **`AZURE_AD_CLIENT_SECRET_PROD`**: Azure AD (Microsoft) Client Secret for production environment

## How to Create GCP Service Account

1. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create github-actions \
     --description="Service account for GitHub Actions CI/CD" \
     --display-name="GitHub Actions"
   ```

2. **Grant Required Roles**:
   ```bash
   PROJECT_ID="your-project-id"
   SA_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SA_EMAIL" \
     --role="roles/editor"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SA_EMAIL" \
     --role="roles/cloudsql.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SA_EMAIL" \
     --role="roles/run.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SA_EMAIL" \
     --role="roles/storage.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SA_EMAIL" \
     --role="roles/artifactregistry.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SA_EMAIL" \
     --role="roles/secretmanager.admin"
   ```

3. **Create and Download Key**:
   ```bash
   gcloud iam service-accounts keys create github-actions-key.json \
     --iam-account=$SA_EMAIL
   ```

4. **Base64 Encode the Key**:
   ```bash
   base64 -i github-actions-key.json
   ```
   
   Copy the output and use it as the value for `GCP_CREDENTIALS` secret.

## Deployment Triggers

The CI/CD pipeline is triggered by:

- **Push to `main` branch**: Deploys to production environment
- **Push to `test` branch**: Deploys to test environment  
- **Manual workflow dispatch**: Allows manual deployment to either environment

## Infrastructure Components

The Terraform configuration creates:

### Shared Infrastructure
- **Artifact Registry**: Docker image repository
- **Cloud SQL**: PostgreSQL database with regional/zonal availability
- **Secret Manager**: Secure secret storage
- **Service Accounts**: IAM for Cloud Run services

### Application Services
- **Django Backend**: Cloud Run service for the Django API
- **Prefect Server**: Cloud Run service for workflow orchestration
- **Frontend Hosting**: Cloud Storage + CDN for React app

### Environment Differences

| Component | Test Environment | Production Environment |
|-----------|------------------|------------------------|
| Cloud SQL Tier | `db-f1-micro` | `db-custom-2-4096` |
| Cloud SQL Availability | `ZONAL` | `REGIONAL` |
| Min Instances | 0 | 1 |
| Max Instances | 3 | 10 |
| CPU Limit | 1000m | 2000m |
| Memory Limit | 2Gi | 4Gi |
| Backup Retention | 3 days | 30 days |
| Deletion Protection | false | true |

## Outputs

After successful deployment, the following URLs are available:

- **Django Backend URL**: `https://{env}-django-backend-*.run.app`
- **Prefect Server URL**: `https://{env}-prefect-server-*.run.app`
- **Frontend URL**: Via Cloud Storage bucket and CDN

## Local Development

For local development, use the existing Docker Compose setup:

```bash
docker-compose -f docker-compose.dev.yml up
```

## Troubleshooting

### Common Issues

1. **Terraform State Conflicts**: Configure remote state backend in GCS
2. **Image Push Failures**: Ensure Artifact Registry repository exists
3. **Cloud SQL Connection Issues**: Verify service account permissions
4. **Secret Access Denied**: Check Secret Manager IAM bindings

### Viewing Logs

```bash
# Cloud Run logs
gcloud run services logs read {service-name} --region={region}

# Cloud SQL logs  
gcloud sql operations list --instance={instance-name}

# Build logs in Cloud Build (if enabled)
gcloud builds list
```

## OAuth Provider Setup

### Google OAuth2 Setup

1. **Create OAuth2 Application**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Select "Web application" as application type
   - Add authorized redirect URIs:
     - Test: `https://{test-env}-django-backend-*.run.app/accounts/google/login/callback/`
     - Production: `https://{prod-env}-django-backend-*.run.app/accounts/google/login/callback/`
   - Note the Client ID and Client Secret

2. **Configure GitHub Secrets**:
   ```
   GOOGLE_OAUTH2_CLIENT_ID_TEST=your-test-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH2_CLIENT_SECRET_TEST=GOCSPX-your-test-client-secret
   GOOGLE_OAUTH2_CLIENT_ID_PROD=your-prod-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH2_CLIENT_SECRET_PROD=GOCSPX-your-prod-client-secret
   ```

### Azure AD (Microsoft) OAuth Setup

1. **Create Azure AD Application**:
   - Go to [Azure Portal](https://portal.azure.com/)
   - Navigate to "Azure Active Directory" > "App registrations"
   - Click "New registration"
   - Set redirect URIs:
     - Test: `https://{test-env}-django-backend-*.run.app/accounts/microsoft/login/callback/`
     - Production: `https://{prod-env}-django-backend-*.run.app/accounts/microsoft/login/callback/`
   - Generate a client secret in "Certificates & secrets"
   - Note the Application (client) ID and Client Secret

2. **Configure GitHub Secrets**:
   ```
   AZURE_AD_CLIENT_ID_TEST=your-test-azure-application-id
   AZURE_AD_CLIENT_SECRET_TEST=your-test-azure-client-secret
   AZURE_AD_CLIENT_ID_PROD=your-prod-azure-application-id
   AZURE_AD_CLIENT_SECRET_PROD=your-prod-azure-client-secret
   ```

### Google Workspace Integration (Optional)

For organizations using Google Workspace, additional configuration may be needed:

1. **Admin SDK API Access**:
   - Enable Google Admin SDK API in Google Cloud Console
   - Create a service account with domain-wide delegation
   - Add scopes in Google Admin Console

2. **Django Settings** (if implementing Workspace features):
   ```python
   # Additional settings for Google Workspace
   GOOGLE_WORKSPACE_DOMAIN = "your-domain.com"
   GOOGLE_WORKSPACE_ADMIN_EMAIL = "admin@your-domain.com"
   ```

**Note**: Google Workspace integration is not currently implemented in the base configuration but can be added for advanced use cases.

## Security Considerations

### OAuth Security Best Practices

1. **Use environment-specific OAuth applications**
2. **Rotate client secrets regularly**
3. **Limit redirect URIs to your actual domains**
4. **Monitor OAuth usage through provider dashboards**
5. **Use HTTPS-only redirect URIs**

### Secret Management

All OAuth credentials are managed through:
- **GitHub Secrets** for CI/CD pipeline
- **GCP Secret Manager** for runtime environment
- **Environment-specific isolation** between test and production

The Terraform infrastructure automatically creates Secret Manager secrets and injects them into Cloud Run services, ensuring secure credential handling throughout the deployment pipeline.