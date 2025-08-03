/**
 * Artifact Registry module for storing Docker images
 * Creates repositories for Django backend and Prefect server images
 */

resource "google_artifact_registry_repository" "repository" {
  repository_id = var.repository_id
  location      = var.location
  format        = "DOCKER"
  project       = var.project_id

  description = var.description

  labels = var.labels

  depends_on = [
    google_project_service.artifactregistry_api
  ]
}

# Enable Artifact Registry API
resource "google_project_service" "artifactregistry_api" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

# IAM binding for Cloud Build to push images
resource "google_artifact_registry_repository_iam_binding" "cloud_build_writer" {
  count = var.enable_cloud_build_access ? 1 : 0

  project    = var.project_id
  location   = google_artifact_registry_repository.repository.location
  repository = google_artifact_registry_repository.repository.name
  role       = "roles/artifactregistry.writer"

  members = [
    "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  ]
}

# IAM binding for Cloud Run to pull images
resource "google_artifact_registry_repository_iam_binding" "cloud_run_reader" {
  count = var.enable_cloud_run_access ? 1 : 0

  project    = var.project_id
  location   = google_artifact_registry_repository.repository.location
  repository = google_artifact_registry_repository.repository.name
  role       = "roles/artifactregistry.reader"

  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  ]
}

# Custom service account access
resource "google_artifact_registry_repository_iam_binding" "custom_service_account" {
  count = length(var.service_account_members)

  project    = var.project_id
  location   = google_artifact_registry_repository.repository.location
  repository = google_artifact_registry_repository.repository.name
  role       = var.service_account_role

  members = var.service_account_members
}

# Get project information
data "google_project" "project" {
  project_id = var.project_id
}