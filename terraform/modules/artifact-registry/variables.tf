variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "repository_id" {
  description = "ID of the Artifact Registry repository"
  type        = string
}

variable "location" {
  description = "Location for the Artifact Registry repository"
  type        = string
  default     = "us-central1"
}

variable "description" {
  description = "Description of the repository"
  type        = string
  default     = "Docker repository for application images"
}

variable "labels" {
  description = "Labels to apply to the repository"
  type        = map(string)
  default     = {}
}

variable "enable_cloud_build_access" {
  description = "Enable Cloud Build to write to this repository"
  type        = bool
  default     = true
}

variable "enable_cloud_run_access" {
  description = "Enable Cloud Run to read from this repository"
  type        = bool
  default     = true
}

variable "service_account_members" {
  description = "List of service account members to grant access"
  type        = list(string)
  default     = []
}

variable "service_account_role" {
  description = "Role to grant to service account members"
  type        = string
  default     = "roles/artifactregistry.reader"
}