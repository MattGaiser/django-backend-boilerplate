output "repository_id" {
  description = "ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.repository.repository_id
}

output "repository_name" {
  description = "Full name of the repository"
  value       = google_artifact_registry_repository.repository.name
}

output "repository_url" {
  description = "URL of the repository for Docker images"
  value       = "${google_artifact_registry_repository.repository.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repository.repository_id}"
}

output "location" {
  description = "Location of the repository"
  value       = google_artifact_registry_repository.repository.location
}