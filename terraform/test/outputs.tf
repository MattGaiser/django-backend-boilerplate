output "django_backend_url" {
  description = "URL of the Django backend service"
  value       = module.django_backend.service_url
}

output "prefect_server_url" {
  description = "URL of the Prefect server"
  value       = module.prefect_server.service_url
}

output "frontend_bucket_name" {
  description = "Name of the frontend bucket"
  value       = module.frontend_hosting.bucket_name
}

output "frontend_url" {
  description = "URL of the frontend"
  value       = module.frontend_hosting.frontend_url
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = module.artifact_registry.repository_url
}

output "database_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = module.database.instance_name
}

output "database_connection_name" {
  description = "Connection name for the Cloud SQL instance"
  value       = module.database.instance_connection_name
}

output "service_account_email" {
  description = "Email of the service account used by applications"
  value       = google_service_account.app_service_account.email
}

output "storage_bucket_name" {
  description = "Name of the application storage bucket"
  value       = module.app_storage.bucket_name
}

output "storage_bucket_url" {
  description = "URL of the application storage bucket"
  value       = module.app_storage.bucket_url
}