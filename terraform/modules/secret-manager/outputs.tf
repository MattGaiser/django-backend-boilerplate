output "secret_ids" {
  description = "Map of secret names to their IDs"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.secret_id }
}

output "secret_names" {
  description = "Map of secret names to their full resource names"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.name }
}

output "secret_versions" {
  description = "Map of secret names to their version resource names"
  value       = { for k, v in google_secret_manager_secret_version.secret_version : k => v.name }
}