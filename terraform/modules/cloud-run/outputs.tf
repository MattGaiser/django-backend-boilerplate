output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.service.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.service.name
}

output "service_id" {
  description = "Full resource ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.service.id
}

output "location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.service.location
}

output "latest_created_revision" {
  description = "Latest created revision name"
  value       = google_cloud_run_v2_service.service.latest_created_revision
}

output "latest_ready_revision" {
  description = "Latest ready revision name"
  value       = google_cloud_run_v2_service.service.latest_ready_revision
}