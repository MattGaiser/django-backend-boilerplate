output "bucket_name" {
  description = "Name of the main application assets bucket"
  value       = google_storage_bucket.app_assets.name
}

output "bucket_url" {
  description = "URL of the main application assets bucket"
  value       = google_storage_bucket.app_assets.url
}

output "bucket_self_link" {
  description = "Self-link of the main application assets bucket"
  value       = google_storage_bucket.app_assets.self_link
}

output "additional_bucket_names" {
  description = "Names of additional buckets created"
  value       = { for k, v in google_storage_bucket.additional_buckets : k => v.name }
}

output "additional_bucket_urls" {
  description = "URLs of additional buckets created"
  value       = { for k, v in google_storage_bucket.additional_buckets : k => v.url }
}