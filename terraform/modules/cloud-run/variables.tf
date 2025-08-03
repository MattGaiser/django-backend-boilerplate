variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "location" {
  description = "GCP region for the Cloud Run service"
  type        = string
  default     = "us-central1"
}

variable "image_url" {
  description = "Container image URL from Artifact Registry"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "cpu_limit" {
  description = "CPU limit for the container"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for the container"
  type        = string
  default     = "2Gi"
}

variable "cpu_idle" {
  description = "Whether CPU is allocated during idle"
  type        = bool
  default     = false
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets from Secret Manager"
  type = map(object({
    secret_name = string
    version     = string
  }))
  default = {}
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "cloud_sql_connections" {
  description = "Cloud SQL connection string (project:region:instance)"
  type        = string
  default     = null
}

variable "health_check_path" {
  description = "Path for health checks"
  type        = string
  default     = "/health/"
}

variable "allow_public_access" {
  description = "Whether to allow public access to the service"
  type        = bool
  default     = true
}

variable "custom_domain" {
  description = "Custom domain for the service"
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels to apply to the Cloud Run service"
  type        = map(string)
  default     = {}
}