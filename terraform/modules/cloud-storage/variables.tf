variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "bucket_name" {
  description = "Name of the main application assets bucket"
  type        = string
}

variable "location" {
  description = "Bucket location (region or multi-region)"
  type        = string
  default     = "US"
}

variable "enable_versioning" {
  description = "Enable versioning on the main bucket"
  type        = bool
  default     = true
}

variable "enable_public_access" {
  description = "Enable public access to bucket objects"
  type        = bool
  default     = false
}

variable "backend_service_accounts" {
  description = "List of backend service accounts that need full access to the bucket"
  type        = list(string)
  default     = []
}

variable "readonly_service_accounts" {
  description = "List of service accounts that need read-only access to the bucket"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules for the bucket"
  type = list(object({
    condition = object({
      age                   = optional(number)
      created_before        = optional(string)
      with_state           = optional(string)
      matches_storage_class = optional(list(string))
      num_newer_versions   = optional(number)
    })
    action = object({
      type          = string
      storage_class = optional(string)
    })
  }))
  default = []
}

variable "cors_rules" {
  description = "CORS rules for the bucket"
  type = list(object({
    origin          = list(string)
    method          = list(string)
    response_header = list(string)
    max_age_seconds = number
  }))
  default = []
}

variable "additional_buckets" {
  description = "Additional buckets to create with specific configurations"
  type = map(object({
    name              = string
    enable_versioning = optional(bool, true)
    labels           = optional(map(string), {})
    service_accounts = list(object({
      member = string
      role   = string
    }))
  }))
  default = {}
}