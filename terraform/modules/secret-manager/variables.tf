variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "secrets" {
  description = "Map of secrets to create"
  type = map(object({
    value  = string
    labels = map(string)
  }))
  default = {}
}

variable "labels" {
  description = "Default labels to apply to all secrets"
  type        = map(string)
  default     = {}
}

variable "cloud_run_service_accounts" {
  description = "List of Cloud Run service accounts that need access to secrets"
  type        = list(string)
  default     = []
}

variable "additional_service_accounts" {
  description = "Additional service accounts that need access to secrets"
  type        = list(string)
  default     = []
}