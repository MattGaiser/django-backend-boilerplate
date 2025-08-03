terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Backend configuration for Terraform state
  # This should be configured per environment
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "terraform/state/test"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Local values for test environment
locals {
  environment = "test"
  labels = {
    environment = local.environment
    project     = "django-backend-boilerplate"
    managed_by  = "terraform"
  }

  # Test-specific configurations
  sql_tier            = "db-f1-micro"
  min_instances       = 0
  max_instances       = 3
  deletion_protection = false
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

  availability_type      = "ZONAL"
  deletion_protection    = local.deletion_protection
  backup_retention_count = 3

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

  environment_variables = {
    DJANGO_ENV    = "test"
    USE_POSTGRES  = "true"
    POSTGRES_HOST = "/cloudsql/${module.database.instance_connection_name}"
    POSTGRES_DB   = module.database.database_name
    POSTGRES_USER = module.database.database_user
    POSTGRES_PORT = "5432"
    ALLOWED_HOSTS = "*.run.app,${local.environment}-django-backend-*.run.app"
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
  }

  cloud_sql_connections = module.database.instance_connection_name
  health_check_path     = "/health/"

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

  min_instances = local.min_instances
  max_instances = 2

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

  project_id  = var.project_id
  bucket_name = "${local.environment}-frontend-${random_id.bucket_suffix.hex}"
  labels      = local.labels
}

# Random suffix for bucket name (must be globally unique)
resource "random_id" "bucket_suffix" {
  byte_length = 4
}