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
  description = "Django secret key for production environment"
  type        = string
  sensitive   = true
}

variable "database_password" {
  description = "Database password for production environment"
  type        = string
  sensitive   = true
}

variable "custom_domains" {
  description = "Custom domains for the production deployment"
  type        = list(string)
  default     = null
}

variable "enable_https" {
  description = "Enable HTTPS for the frontend"
  type        = bool
  default     = false
}

variable "ssl_certificates" {
  description = "SSL certificates for HTTPS (if enabled)"
  type        = list(string)
  default     = []
}