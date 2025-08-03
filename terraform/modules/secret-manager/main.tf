/**
 * Secret Manager module for managing application secrets
 * Creates secrets for Django and other services
 */

resource "google_secret_manager_secret" "secret" {
  for_each = var.secrets

  secret_id = each.key
  project   = var.project_id

  labels = merge(var.labels, each.value.labels)

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.secretmanager_api
  ]
}

resource "google_secret_manager_secret_version" "secret_version" {
  for_each = var.secrets

  secret      = google_secret_manager_secret.secret[each.key].id
  secret_data = each.value.value
}

# Enable Secret Manager API
resource "google_project_service" "secretmanager_api" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

# IAM binding for Cloud Run services to access secrets
resource "google_secret_manager_secret_iam_binding" "cloud_run_access" {
  for_each = var.secrets

  project   = var.project_id
  secret_id = google_secret_manager_secret.secret[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = var.cloud_run_service_accounts
}

# IAM binding for additional service accounts
resource "google_secret_manager_secret_iam_binding" "additional_access" {
  for_each = {
    for combo in flatten([
      for secret_key, secret_value in var.secrets : [
        for sa in var.additional_service_accounts : {
          secret_key = secret_key
          member     = sa
        }
      ]
    ]) : "${combo.secret_key}-${combo.member}" => combo
  }

  project   = var.project_id
  secret_id = google_secret_manager_secret.secret[each.value.secret_key].secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = [each.value.member]
}