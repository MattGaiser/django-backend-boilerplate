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

variable "google_oauth2_client_id" {
  description = "Google OAuth2 Client ID for social authentication"
  type        = string
  sensitive   = true
}

variable "google_oauth2_client_secret" {
  description = "Google OAuth2 Client Secret for social authentication"
  type        = string
  sensitive   = true
}

variable "azure_ad_client_id" {
  description = "Azure AD (Microsoft) Client ID for social authentication"
  type        = string
  sensitive   = true
}

variable "azure_ad_client_secret" {
  description = "Azure AD (Microsoft) Client Secret for social authentication"
  type        = string
  sensitive   = true
}