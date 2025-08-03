/**
 * Frontend hosting module using Cloud Storage + CDN
 * Alternative to Firebase for static React app hosting
 */

# Create Cloud Storage bucket for frontend assets
resource "google_storage_bucket" "frontend_bucket" {
  name     = var.bucket_name
  location = var.bucket_location
  project  = var.project_id

  uniform_bucket_level_access = true

  website {
    main_page_suffix = var.main_page_suffix
    not_found_page   = var.not_found_page
  }

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = var.labels

  depends_on = [
    google_project_service.storage_api
  ]
}

# Make bucket publicly readable
resource "google_storage_bucket_iam_binding" "public_read" {
  bucket = google_storage_bucket.frontend_bucket.name
  role   = "roles/storage.objectViewer"

  members = [
    "allUsers",
  ]
}

# Create Cloud CDN and Load Balancer
resource "google_compute_global_address" "frontend_ip" {
  name    = "${var.bucket_name}-ip"
  project = var.project_id
}

resource "google_compute_backend_bucket" "frontend_backend" {
  name        = "${var.bucket_name}-backend"
  description = "Backend bucket for frontend assets"
  bucket_name = google_storage_bucket.frontend_bucket.name
  enable_cdn  = var.enable_cdn
  project     = var.project_id

  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = var.cdn_default_ttl
    max_ttl                      = var.cdn_max_ttl
    client_ttl                   = var.cdn_client_ttl
    negative_caching             = true
    serve_while_stale            = var.cdn_serve_while_stale
  }
}

resource "google_compute_url_map" "frontend_url_map" {
  name            = "${var.bucket_name}-url-map"
  description     = "URL map for frontend"
  default_service = google_compute_backend_bucket.frontend_backend.id
  project         = var.project_id

  # Route all paths to the bucket, with fallback to index.html for SPA
  host_rule {
    hosts        = var.custom_domains
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_bucket.frontend_backend.id

    # Serve index.html for SPA routes
    path_rule {
      paths   = ["/*"]
      service = google_compute_backend_bucket.frontend_backend.id
    }
  }
}

resource "google_compute_target_https_proxy" "frontend_https_proxy" {
  count = var.enable_https ? 1 : 0

  name             = "${var.bucket_name}-https-proxy"
  url_map          = google_compute_url_map.frontend_url_map.id
  ssl_certificates = var.ssl_certificates
  project          = var.project_id
}

resource "google_compute_target_http_proxy" "frontend_http_proxy" {
  name    = "${var.bucket_name}-http-proxy"
  url_map = google_compute_url_map.frontend_url_map.id
  project = var.project_id
}

resource "google_compute_global_forwarding_rule" "frontend_https_forwarding_rule" {
  count = var.enable_https ? 1 : 0

  name                  = "${var.bucket_name}-https-forwarding-rule"
  target                = google_compute_target_https_proxy.frontend_https_proxy[0].id
  port_range            = "443"
  ip_address            = google_compute_global_address.frontend_ip.address
  load_balancing_scheme = "EXTERNAL"
  project               = var.project_id
}

resource "google_compute_global_forwarding_rule" "frontend_http_forwarding_rule" {
  name                  = "${var.bucket_name}-http-forwarding-rule"
  target                = google_compute_target_http_proxy.frontend_http_proxy.id
  port_range            = "80"
  ip_address            = google_compute_global_address.frontend_ip.address
  load_balancing_scheme = "EXTERNAL"
  project               = var.project_id
}

# Enable required APIs
resource "google_project_service" "storage_api" {
  project = var.project_id
  service = "storage.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

resource "google_project_service" "compute_api" {
  project = var.project_id
  service = "compute.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}