variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
}

variable "region" {
  description = "GCP region for the Cloud SQL instance"
  type        = string
  default     = "us-central1"
}

variable "database_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_16"
}

variable "tier" {
  description = "Machine type for the instance"
  type        = string
  default     = "db-f1-micro"
}

variable "availability_type" {
  description = "Availability type (REGIONAL or ZONAL)"
  type        = string
  default     = "ZONAL"
}

variable "disk_type" {
  description = "Disk type (PD_SSD or PD_HDD)"
  type        = string
  default     = "PD_SSD"
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 20
}

variable "disk_autoresize" {
  description = "Enable automatic disk size increase"
  type        = bool
  default     = true
}

variable "backup_enabled" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_start_time" {
  description = "Backup start time in HH:MM format"
  type        = string
  default     = "02:00"
}

variable "point_in_time_recovery_enabled" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "backup_retention_count" {
  description = "Number of backups to retain"
  type        = number
  default     = 7
}

variable "ipv4_enabled" {
  description = "Enable IPv4 access"
  type        = bool
  default     = true
}

variable "private_network" {
  description = "VPC network for private IP (optional)"
  type        = string
  default     = null
}

variable "require_ssl" {
  description = "Require SSL connections"
  type        = bool
  default     = true
}

variable "authorized_networks" {
  description = "List of authorized networks"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "database_name" {
  description = "Name of the Django database"
  type        = string
  default     = "django_db"
}

variable "database_user" {
  description = "Django database user"
  type        = string
  default     = "django_user"
}

variable "database_password" {
  description = "Django database password"
  type        = string
  sensitive   = true
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "log_statement" {
  description = "Log statement setting"
  type        = string
  default     = "all"
}

variable "log_min_duration_statement" {
  description = "Log minimum duration statement (ms)"
  type        = string
  default     = "1000"
}

variable "query_insights_enabled" {
  description = "Enable query insights"
  type        = bool
  default     = true
}

variable "record_application_tags" {
  description = "Record application tags in query insights"
  type        = bool
  default     = true
}

variable "record_client_address" {
  description = "Record client address in query insights"
  type        = bool
  default     = true
}

variable "maintenance_window_day" {
  description = "Maintenance window day (1-7, 1=Monday)"
  type        = number
  default     = 7
}

variable "maintenance_window_hour" {
  description = "Maintenance window hour (0-23)"
  type        = number
  default     = 3
}

variable "maintenance_window_update_track" {
  description = "Maintenance window update track"
  type        = string
  default     = "stable"
}

variable "labels" {
  description = "Labels to apply to the Cloud SQL instance"
  type        = map(string)
  default     = {}
}