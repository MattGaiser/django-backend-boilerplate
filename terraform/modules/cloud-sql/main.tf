/**
 * Cloud SQL module for PostgreSQL database
 * Supports both test and production configurations
 */

resource "google_sql_database_instance" "main" {
  name             = var.instance_name
  database_version = var.database_version
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_type         = var.disk_type
    disk_size         = var.disk_size
    disk_autoresize   = var.disk_autoresize

    backup_configuration {
      enabled                        = var.backup_enabled
      start_time                     = var.backup_start_time
      point_in_time_recovery_enabled = var.point_in_time_recovery_enabled
      backup_retention_settings {
        retained_backups = var.backup_retention_count
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = var.ipv4_enabled
      private_network = var.private_network
      require_ssl     = var.require_ssl

      dynamic "authorized_networks" {
        for_each = var.authorized_networks
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.value
        }
      }
    }

    database_flags {
      name  = "log_statement"
      value = var.log_statement
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = var.log_min_duration_statement
    }

    insights_config {
      query_insights_enabled  = var.query_insights_enabled
      record_application_tags = var.record_application_tags
      record_client_address   = var.record_client_address
    }

    maintenance_window {
      day          = var.maintenance_window_day
      hour         = var.maintenance_window_hour
      update_track = var.maintenance_window_update_track
    }

    user_labels = var.labels
  }

  deletion_protection = var.deletion_protection

  depends_on = [
    google_project_service.sqladmin_api,
    google_project_service.compute_api,
    google_project_service.servicenetworking_api
  ]
}

# Create the Django database
resource "google_sql_database" "django_db" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

# Create the Django user
resource "google_sql_user" "django_user" {
  name     = var.database_user
  instance = google_sql_database_instance.main.name
  password = var.database_password
  project  = var.project_id
}

# Enable required APIs
resource "google_project_service" "sqladmin_api" {
  project = var.project_id
  service = "sqladmin.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

resource "google_project_service" "compute_api" {
  project = var.project_id
  service = "compute.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

resource "google_project_service" "servicenetworking_api" {
  project = var.project_id
  service = "servicenetworking.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

# Create a private IP allocation for VPC peering (if using private network)
resource "google_compute_global_address" "private_ip_allocation" {
  count = var.private_network != null ? 1 : 0

  name          = "${var.instance_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.private_network
  project       = var.project_id
}

# Create VPC peering connection (if using private network)
resource "google_service_networking_connection" "private_vpc_connection" {
  count = var.private_network != null ? 1 : 0

  network                 = var.private_network
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_allocation[0].name]
}