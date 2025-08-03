output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.app_assets.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.app_assets.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.app_assets.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.app_assets.bucket_regional_domain_name
}

output "backend_policy_arn" {
  description = "ARN of the IAM policy for backend access"
  value       = aws_iam_policy.s3_backend_policy.arn
}