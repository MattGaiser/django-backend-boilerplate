/**
 * Cloud Run module for Django backend and Prefect server
 * Supports multiple services with shared configuration
 */

resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.location
  project  = var.project_id

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image_url

      # Environment variables
      dynamic "env" {
        for_each = var.environment_variables
        content {
          name  = env.key
          value = env.value
        }
      }

      # Secrets from Secret Manager
      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_name
              version = env.value.version
            }
          }
        }
      }

      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = var.cpu_idle
      }

      # Health check
      startup_probe {
        http_get {
          path = var.health_check_path
          port = var.container_port
        }
        initial_delay_seconds = 30
        timeout_seconds      = 10
        period_seconds       = 10
        failure_threshold    = 3
      }

      liveness_probe {
        http_get {
          path = var.health_check_path
          port = var.container_port
        }
        initial_delay_seconds = 60
        timeout_seconds      = 10
        period_seconds       = 30
        failure_threshold    = 3
      }
    }

    # Service account for accessing other GCP services
    service_account = var.service_account_email

    # Annotations for Cloud SQL connections if provided
    annotations = var.cloud_sql_connections != null ? {
      "run.googleapis.com/cloudsql-instances" = var.cloud_sql_connections
    } : {}
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.cloudrun_api,
    google_project_service.compute_api
  ]
}

# Enable required APIs
resource "google_project_service" "cloudrun_api" {
  project = var.project_id
  service = "run.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

resource "google_project_service" "compute_api" {
  project = var.project_id
  service = "compute.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

# IAM binding to allow public access (can be customized per service)
resource "google_cloud_run_service_iam_binding" "public_access" {
  count = var.allow_public_access ? 1 : 0

  location = google_cloud_run_v2_service.service.location
  project  = google_cloud_run_v2_service.service.project
  service  = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"

  members = [
    "allUsers",
  ]
}

# Custom domain mapping if provided
resource "google_cloud_run_domain_mapping" "domain" {
  count = var.custom_domain != null ? 1 : 0

  location = google_cloud_run_v2_service.service.location
  name     = var.custom_domain

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.service.name
  }
}