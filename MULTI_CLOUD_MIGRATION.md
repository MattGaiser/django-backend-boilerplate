# Multi-Cloud Migration Guide

This guide provides instructions for migrating the Django backend between different cloud providers to reduce vendor lock-in concerns.

## Current Multi-Cloud Support

The application has been architected to support multiple cloud providers with minimal configuration changes:

### Supported Cloud Providers

- **Google Cloud Platform (GCP)** - Primary implementation
- **Amazon Web Services (AWS)** - Full support via abstraction layer
- **Microsoft Azure** - Full support via abstraction layer

### Cloud-Agnostic Components

✅ **Easily Portable (No Lock-in)**
- Django application code
- PostgreSQL database schema
- Docker containers
- API endpoints and business logic
- User authentication and RBAC
- Prefect workflows

⚠️ **Moderate Effort Required**
- File storage (abstracted but requires configuration)
- OAuth provider setup
- CI/CD pipelines (provider-specific)
- Secret management
- Environment configuration

🔄 **Requires Migration Work**
- Infrastructure as Code (provider-specific Terraform)
- Cloud-specific services (managed databases, container platforms)
- Monitoring and logging (if using cloud-specific solutions)
- Networking and security configurations

## Migration Process

### Phase 1: Configuration Migration (1-2 days)

1. **Update Environment Configuration**
   ```bash
   # Copy the appropriate environment template
   cp .env.aws.example .env
   # OR
   cp .env.azure.example .env
   # OR  
   cp .env.gcp.example .env
   
   # Update with your cloud provider credentials
   nano .env
   ```

2. **Update Cloud Provider Setting**
   ```bash
   # In your .env file
   CLOUD_PROVIDER=aws  # or azure, gcp
   ```

3. **Test Local Development**
   ```bash
   # The application should work with any cloud provider
   docker-compose up
   ```

### Phase 2: Infrastructure Migration (1-2 weeks)

#### Option A: Manual Infrastructure Setup

1. **Database Migration**
   - Export data from current database
   - Set up new managed database service
   - Import data to new database
   - Update connection settings

2. **File Storage Migration**
   - Use cloud provider's migration tools:
     - AWS: `aws s3 sync gs://source-bucket s3://target-bucket`
     - Azure: `azcopy sync "gs://source-bucket" "https://account.blob.core.windows.net/container"`
   - Update storage configuration

3. **Container Platform Setup**
   - Build and push images to new container registry
   - Set up container platform (ECS, AKS, Cloud Run)
   - Deploy application

#### Option B: Infrastructure as Code (Recommended)

1. **Use Terraform Templates**
   ```bash
   # For AWS
   cd terraform/aws/production
   terraform init
   terraform plan
   terraform apply
   
   # For Azure (when implemented)
   cd terraform/azure/production
   terraform init
   terraform plan  
   terraform apply
   ```

2. **Deploy via CI/CD**
   ```bash
   # Use the appropriate workflow
   .github/workflows/deploy-aws.yml
   .github/workflows/deploy-azure.yml (when implemented)
   ```

### Phase 3: Validation and Cutover (2-3 days)

1. **Test All Functionality**
   - User authentication and authorization
   - File upload/download operations
   - Database operations
   - API endpoints
   - Prefect workflows

2. **Performance Testing**
   - Load testing
   - Security scanning
   - Monitor resource usage

3. **DNS and Traffic Cutover**
   - Update DNS records
   - Monitor application health
   - Rollback plan ready

## Provider-Specific Migration Details

### Migrating to AWS

**Services Mapping:**
- Cloud Run → ECS Fargate
- Cloud SQL → RDS PostgreSQL
- Cloud Storage → S3
- Secret Manager → Systems Manager Parameter Store
- Cloud Build → CodeBuild
- IAM → AWS IAM

**Required Setup:**
1. AWS Account with appropriate permissions
2. ECR repository for container images
3. VPC and networking setup
4. RDS instance with PostgreSQL
5. S3 bucket with appropriate policies
6. ECS cluster and service definition

**Configuration Changes:**
```bash
# Update .env file
CLOUD_PROVIDER=aws
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
CLOUD_STORAGE_BUCKET_NAME=your-s3-bucket
RDS_HOSTNAME=your-rds-endpoint.region.rds.amazonaws.com
```

### Migrating to Azure

**Services Mapping:**
- Cloud Run → Azure Container Instances / App Service
- Cloud SQL → Azure Database for PostgreSQL
- Cloud Storage → Azure Blob Storage
- Secret Manager → Azure Key Vault
- Cloud Build → Azure DevOps / GitHub Actions
- IAM → Azure AD / RBAC

**Required Setup:**
1. Azure subscription with Resource Group
2. Azure Container Registry
3. Azure Database for PostgreSQL
4. Storage Account with Blob containers
5. Azure Key Vault for secrets
6. App Service or Container Instances

**Configuration Changes:**
```bash
# Update .env file
CLOUD_PROVIDER=azure
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your_key
CLOUD_STORAGE_BUCKET_NAME=your-container
AZURE_DB_HOST=your-server.postgres.database.azure.com
```

## Cost Comparison

### Estimated Monthly Costs (Small/Medium App)

| Service | GCP | AWS | Azure |
|---------|-----|-----|--------|
| Container Platform | Cloud Run: $20-50 | ECS Fargate: $25-60 | Container Instances: $30-70 |
| Database | Cloud SQL: $50-150 | RDS: $60-180 | Database for PostgreSQL: $55-170 |
| Storage | Cloud Storage: $5-20 | S3: $5-25 | Blob Storage: $6-22 |
| Load Balancer | $18 | ALB: $25 | Load Balancer: $20 |
| **Total** | **$93-238** | **$115-290** | **$111-282** |

*Prices are estimates and vary by region and usage patterns.*

## Rollback Strategy

### Quick Rollback (< 1 hour)
1. Revert DNS changes
2. Scale up old infrastructure if still running
3. Restore database from backup if needed

### Full Rollback (2-4 hours)
1. Restore full infrastructure in original cloud
2. Restore database from latest backup
3. Restore file storage from backup
4. Update all configuration
5. Redeploy application

## Best Practices for Multi-Cloud

### 1. Configuration Management
- Use environment variables for all cloud-specific settings
- Never hardcode cloud provider names in application code
- Use the cloud configuration abstraction layer

### 2. Data Backup Strategy
- Regular automated database backups
- Cross-cloud storage replication for critical files
- Document backup and restore procedures

### 3. Infrastructure as Code
- Maintain Terraform templates for all supported clouds
- Version control all infrastructure changes
- Test infrastructure changes in staging first

### 4. Monitoring and Alerting
- Use cloud-agnostic monitoring tools where possible
- Implement health checks that work across providers
- Set up alerts for key application metrics

### 5. Security Considerations
- Use cloud provider IAM best practices
- Encrypt data in transit and at rest
- Regular security audits and updates
- Implement principle of least privilege

## Troubleshooting Common Issues

### Storage Access Errors
```bash
# Check cloud provider configuration
python manage.py shell
>>> from core.storage import get_default_storage
>>> storage = get_default_storage()
>>> storage.file_exists('test.txt')
```

### Database Connection Issues
```bash
# Test database connectivity
python manage.py dbshell
# OR
python manage.py check --database default
```

### Authentication Provider Issues
```bash
# Verify OAuth configuration
python manage.py shell
>>> from django.conf import settings
>>> print(settings.SOCIALACCOUNT_PROVIDERS)
```

## Future Enhancements

### Planned Features
- [ ] Azure Terraform modules
- [ ] Kubernetes deployment templates
- [ ] Multi-cloud disaster recovery
- [ ] Cost optimization recommendations
- [ ] Automated migration scripts
- [ ] Cross-cloud data synchronization

### Community Contributions Welcome
- Additional cloud provider support
- Cost optimization strategies
- Migration automation tools
- Performance benchmarking across clouds

## Support

For migration assistance or questions:
- Review the GitHub Issues for common problems
- Check the deployment documentation for your target cloud
- Test migrations in a staging environment first
- Consider professional services for complex migrations