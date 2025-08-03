output "bucket_name" {
  description = "Name of the Cloud Storage bucket"
  value       = google_storage_bucket.frontend_bucket.name
}

output "bucket_url" {
  description = "URL of the Cloud Storage bucket"
  value       = google_storage_bucket.frontend_bucket.url
}

output "frontend_ip" {
  description = "Global IP address for the frontend"
  value       = google_compute_global_address.frontend_ip.address
}

output "frontend_url" {
  description = "URL of the frontend (HTTP)"
  value       = "http://${google_compute_global_address.frontend_ip.address}"
}

output "frontend_https_url" {
  description = "URL of the frontend (HTTPS)"
  value       = var.enable_https ? "https://${google_compute_global_address.frontend_ip.address}" : null
}

output "backend_bucket_name" {
  description = "Name of the backend bucket"
  value       = google_compute_backend_bucket.frontend_backend.name
}