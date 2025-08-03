output "instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "instance_connection_name" {
  description = "Connection name for the Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "private_ip_address" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "public_ip_address" {
  description = "Public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

output "database_name" {
  description = "Name of the Django database"
  value       = google_sql_database.django_db.name
}

output "database_user" {
  description = "Django database user"
  value       = google_sql_user.django_user.name
}

output "instance_id" {
  description = "ID of the Cloud SQL instance"
  value       = google_sql_database_instance.main.id
}

output "self_link" {
  description = "Self-link of the Cloud SQL instance"
  value       = google_sql_database_instance.main.self_link
}