terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Backend configuration for Terraform state
  # This should be configured per environment
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "terraform/state/prod"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Local values for production environment
locals {
  environment = "prod"
  labels = {
    environment = local.environment
    project     = "django-backend-boilerplate"
    managed_by  = "terraform"
  }
  
  # Production-specific configurations
  sql_tier            = "db-custom-2-4096"  # 2 vCPU, 4GB RAM
  min_instances       = 1
  max_instances       = 10
  deletion_protection = true
}

# Create service account for Cloud Run services
resource "google_service_account" "app_service_account" {
  account_id   = "${local.environment}-app-sa"
  display_name = "Service account for ${local.environment} applications"
  project      = var.project_id
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "app_service_account_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

resource "google_project_iam_member" "app_service_account_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

# Artifact Registry for Docker images
module "artifact_registry" {
  source = "../modules/artifact-registry"

  project_id    = var.project_id
  repository_id = "${local.environment}-docker-repo"
  location      = var.region
  description   = "Docker repository for ${local.environment} environment"
  labels        = local.labels

  service_account_members = [
    "serviceAccount:${google_service_account.app_service_account.email}"
  ]
}

# Secret Manager for application secrets
module "secrets" {
  source = "../modules/secret-manager"

  project_id = var.project_id
  labels     = local.labels

  secrets = {
    django-secret-key = {
      value  = var.django_secret_key
      labels = {}
    }
    database-password = {
      value  = var.database_password
      labels = {}
    }
    google-oauth2-client-id = {
      value  = var.google_oauth2_client_id
      labels = {}
    }
    google-oauth2-client-secret = {
      value  = var.google_oauth2_client_secret
      labels = {}
    }
    azure-ad-client-id = {
      value  = var.azure_ad_client_id
      labels = {}
    }
    azure-ad-client-secret = {
      value  = var.azure_ad_client_secret
      labels = {}
    }
  }

  cloud_run_service_accounts = [
    "serviceAccount:${google_service_account.app_service_account.email}"
  ]
}

# Cloud SQL database
module "database" {
  source = "../modules/cloud-sql"

  project_id        = var.project_id
  instance_name     = "${local.environment}-postgres"
  region            = var.region
  tier              = local.sql_tier
  database_name     = "django_${local.environment}_db"
  database_user     = "django_${local.environment}_user"
  database_password = var.database_password

  availability_type      = "REGIONAL"  # High availability for production
  deletion_protection    = local.deletion_protection
  backup_retention_count = 30  # Keep backups for 30 days

  labels = local.labels
}

# Django backend Cloud Run service
module "django_backend" {
  source = "../modules/cloud-run"

  project_id            = var.project_id
  service_name          = "${local.environment}-django-backend"
  location              = var.region
  image_url             = "${module.artifact_registry.repository_url}/django-backend:latest"
  service_account_email = google_service_account.app_service_account.email

  min_instances = local.min_instances
  max_instances = local.max_instances

  # Production resource limits
  cpu_limit    = "2000m"  # 2 vCPU
  memory_limit = "4Gi"    # 4GB RAM

  environment_variables = {
    DJANGO_ENV        = "production"
    USE_POSTGRES      = "true"
    POSTGRES_HOST     = "/cloudsql/${module.database.instance_connection_name}"
    POSTGRES_DB       = module.database.database_name
    POSTGRES_USER     = module.database.database_user
    POSTGRES_PORT     = "5432"
    ALLOWED_HOSTS     = var.custom_domains != null ? join(",", var.custom_domains) : "*.run.app,${local.environment}-django-backend-*.run.app"
  }

  secrets = {
    SECRET_KEY = {
      secret_name = module.secrets.secret_ids["django-secret-key"]
      version     = "latest"
    }
    POSTGRES_PASSWORD = {
      secret_name = module.secrets.secret_ids["database-password"]
      version     = "latest"
    }
    GOOGLE_OAUTH2_CLIENT_ID = {
      secret_name = module.secrets.secret_ids["google-oauth2-client-id"]
      version     = "latest"
    }
    GOOGLE_OAUTH2_CLIENT_SECRET = {
      secret_name = module.secrets.secret_ids["google-oauth2-client-secret"]
      version     = "latest"
    }
    AZURE_AD_CLIENT_ID = {
      secret_name = module.secrets.secret_ids["azure-ad-client-id"]
      version     = "latest"
    }
    AZURE_AD_CLIENT_SECRET = {
      secret_name = module.secrets.secret_ids["azure-ad-client-secret"]
      version     = "latest"
    }
  }

  cloud_sql_connections = module.database.instance_connection_name
  health_check_path     = "/api/v1/health/"

  labels = local.labels
}

# Prefect server Cloud Run service
module "prefect_server" {
  source = "../modules/cloud-run"

  project_id            = var.project_id
  service_name          = "${local.environment}-prefect-server"
  location              = var.region
  image_url             = "${module.artifact_registry.repository_url}/prefect-server:latest"
  service_account_email = google_service_account.app_service_account.email
  container_port        = 4200

  min_instances = 1  # Always keep at least one instance running
  max_instances = 3

  # Production resource limits
  cpu_limit    = "1000m"  # 1 vCPU
  memory_limit = "2Gi"    # 2GB RAM

  environment_variables = {
    PREFECT_API_DATABASE_CONNECTION_URL = "postgresql://${module.database.database_user}:${var.database_password}@/${module.database.database_name}?host=/cloudsql/${module.database.instance_connection_name}"
    PREFECT_API_URL                     = "http://0.0.0.0:4200/api"
    PREFECT_SERVER_API_HOST             = "0.0.0.0"
    PREFECT_SERVER_API_PORT             = "4200"
  }

  secrets = {
    PREFECT_API_DATABASE_PASSWORD = {
      secret_name = module.secrets.secret_ids["database-password"]
      version     = "latest"
    }
  }

  cloud_sql_connections = module.database.instance_connection_name
  health_check_path     = "/api/health"

  labels = local.labels
}

# Frontend hosting (Cloud Storage + CDN)
module "frontend_hosting" {
  source = "../modules/frontend-hosting"

  project_id    = var.project_id
  bucket_name   = "${local.environment}-frontend-${random_id.bucket_suffix.hex}"
  enable_https  = var.enable_https
  custom_domains = var.custom_domains
  ssl_certificates = var.ssl_certificates
  labels        = local.labels
}

# Random suffix for bucket name (must be globally unique)
resource "random_id" "bucket_suffix" {
  byte_length = 4
}