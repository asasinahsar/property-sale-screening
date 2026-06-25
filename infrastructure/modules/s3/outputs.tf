output "bucket_name" {
  description = "S3 バケット名（ECS タスクの環境変数 S3_BUCKET_NAME に設定）"
  value       = aws_s3_bucket.documents.id
}

output "bucket_arn" {
  description = "S3 バケット ARN（ECS タスクロールの IAM ポリシーで使用）"
  value       = aws_s3_bucket.documents.arn
}
