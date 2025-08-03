/**
 * Cloud Storage module for managing GCS buckets with RBAC
 * Creates storage buckets for application assets with organization-scoped access
 */

# Enable Cloud Storage API
resource "google_project_service" "storage_api" {
  project = var.project_id
  service = "storage.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Main application assets bucket
resource "google_storage_bucket" "app_assets" {
  name     = var.bucket_name
  project  = var.project_id
  location = var.location

  # Versioning for data protection
  versioning {
    enabled = var.enable_versioning
  }

  # Lifecycle rules to manage storage costs
  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules
    content {
      condition {
        age                   = lookup(lifecycle_rule.value.condition, "age", null)
        created_before        = lookup(lifecycle_rule.value.condition, "created_before", null)
        with_state           = lookup(lifecycle_rule.value.condition, "with_state", null)
        matches_storage_class = lookup(lifecycle_rule.value.condition, "matches_storage_class", null)
        num_newer_versions   = lookup(lifecycle_rule.value.condition, "num_newer_versions", null)
      }
      action {
        type          = lifecycle_rule.value.action.type
        storage_class = lookup(lifecycle_rule.value.action, "storage_class", null)
      }
    }
  }

  # CORS configuration for web uploads
  dynamic "cors" {
    for_each = var.cors_rules
    content {
      origin          = cors.value.origin
      method          = cors.value.method
      response_header = cors.value.response_header
      max_age_seconds = cors.value.max_age_seconds
    }
  }

  # Uniform bucket-level access for better RBAC control
  uniform_bucket_level_access = true

  labels = var.labels

  depends_on = [google_project_service.storage_api]
}

# IAM binding for backend service account - Object Admin access
resource "google_storage_bucket_iam_member" "backend_object_admin" {
  count = length(var.backend_service_accounts)

  bucket = google_storage_bucket.app_assets.name
  role   = "roles/storage.objectAdmin"
  member = var.backend_service_accounts[count.index]
}

# IAM binding for backend service account - Legacy Bucket Reader for bucket operations
resource "google_storage_bucket_iam_member" "backend_bucket_reader" {
  count = length(var.backend_service_accounts)

  bucket = google_storage_bucket.app_assets.name
  role   = "roles/storage.legacyBucketReader"
  member = var.backend_service_accounts[count.index]
}

# IAM binding for additional read-only service accounts
resource "google_storage_bucket_iam_member" "readonly_access" {
  count = length(var.readonly_service_accounts)

  bucket = google_storage_bucket.app_assets.name
  role   = "roles/storage.objectViewer"
  member = var.readonly_service_accounts[count.index]
}

# Optional: Public access for specific objects (if needed)
resource "google_storage_bucket_iam_member" "public_access" {
  count = var.enable_public_access ? 1 : 0

  bucket = google_storage_bucket.app_assets.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Create additional buckets for different purposes (if specified)
resource "google_storage_bucket" "additional_buckets" {
  for_each = var.additional_buckets

  name     = each.value.name
  project  = var.project_id
  location = var.location

  versioning {
    enabled = each.value.enable_versioning
  }

  uniform_bucket_level_access = true
  labels                     = merge(var.labels, each.value.labels)

  depends_on = [google_project_service.storage_api]
}

# IAM bindings for additional buckets
resource "google_storage_bucket_iam_member" "additional_bucket_access" {
  for_each = {
    for combo in flatten([
      for bucket_key, bucket_config in var.additional_buckets : [
        for sa in bucket_config.service_accounts : {
          bucket_key = bucket_key
          bucket     = bucket_config.name
          member     = sa.member
          role       = sa.role
        }
      ]
    ]) : "${combo.bucket_key}-${combo.member}-${combo.role}" => combo
  }

  bucket = each.value.bucket
  role   = each.value.role
  member = each.value.member

  depends_on = [google_storage_bucket.additional_buckets]
}