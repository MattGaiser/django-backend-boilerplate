/**
 * AWS S3 module for Django file storage
 * Alternative to Google Cloud Storage for multi-cloud deployments
 */

# S3 bucket for application assets
resource "aws_s3_bucket" "app_assets" {
  bucket = var.bucket_name

  tags = var.tags
}

# Bucket versioning
resource "aws_s3_bucket_versioning" "app_assets_versioning" {
  bucket = aws_s3_bucket.app_assets.id
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

# Bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "app_assets_encryption" {
  bucket = aws_s3_bucket.app_assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access (for private assets)
resource "aws_s3_bucket_public_access_block" "app_assets_pab" {
  bucket = aws_s3_bucket.app_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CORS configuration
resource "aws_s3_bucket_cors_configuration" "app_assets_cors" {
  count = length(var.cors_rules) > 0 ? 1 : 0
  
  bucket = aws_s3_bucket.app_assets.id

  dynamic "cors_rule" {
    for_each = var.cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}

# Lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "app_assets_lifecycle" {
  count = length(var.lifecycle_rules) > 0 ? 1 : 0
  
  bucket = aws_s3_bucket.app_assets.id

  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.status

      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }

      dynamic "transition" {
        for_each = rule.value.transitions
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration != null ? [rule.value.noncurrent_version_expiration] : []
        content {
          noncurrent_days = noncurrent_version_expiration.value.noncurrent_days
        }
      }
    }
  }
}

# IAM policy for backend application access
data "aws_iam_policy_document" "s3_backend_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.app_assets.arn,
      "${aws_s3_bucket.app_assets.arn}/*",
    ]
  }
}

# IAM policy attachment for ECS task role
resource "aws_iam_policy" "s3_backend_policy" {
  name        = "${var.bucket_name}-backend-policy"
  description = "Policy for backend application to access S3 bucket"
  policy      = data.aws_iam_policy_document.s3_backend_policy.json

  tags = var.tags
}