variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "django_secret_key" {
  description = "Django secret key for test environment"
  type        = string
  sensitive   = true
}

variable "database_password" {
  description = "Database password for test environment"
  type        = string
  sensitive   = true
}