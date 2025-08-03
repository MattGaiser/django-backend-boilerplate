variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "bucket_name" {
  description = "Name of the Cloud Storage bucket for frontend assets"
  type        = string
}

variable "bucket_location" {
  description = "Location of the Cloud Storage bucket"
  type        = string
  default     = "US"
}

variable "main_page_suffix" {
  description = "Main page for the website"
  type        = string
  default     = "index.html"
}

variable "not_found_page" {
  description = "404 page for the website"
  type        = string
  default     = "index.html"
}

variable "cors_origins" {
  description = "CORS origins for the bucket"
  type        = list(string)
  default     = ["*"]
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}

variable "enable_cdn" {
  description = "Enable Cloud CDN"
  type        = bool
  default     = true
}

variable "cdn_default_ttl" {
  description = "Default TTL for CDN cache in seconds"
  type        = number
  default     = 3600
}

variable "cdn_max_ttl" {
  description = "Maximum TTL for CDN cache in seconds"
  type        = number
  default     = 86400
}

variable "cdn_client_ttl" {
  description = "Client TTL for CDN cache in seconds"
  type        = number
  default     = 3600
}

variable "cdn_serve_while_stale" {
  description = "Serve stale content while updating"
  type        = number
  default     = 86400
}

variable "custom_domains" {
  description = "Custom domains for the frontend"
  type        = list(string)
  default     = []
}

variable "enable_https" {
  description = "Enable HTTPS"
  type        = bool
  default     = false
}

variable "ssl_certificates" {
  description = "SSL certificates for HTTPS"
  type        = list(string)
  default     = []
}