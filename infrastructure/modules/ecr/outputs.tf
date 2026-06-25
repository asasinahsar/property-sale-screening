output "repository_url" {
  description = "ECR リポジトリ URL（GitHub Actions の docker push 先）"
  value       = aws_ecr_repository.backend.repository_url
}

output "repository_arn" {
  description = "ECR リポジトリ ARN（IAM ポリシーで使用）"
  value       = aws_ecr_repository.backend.arn
}
