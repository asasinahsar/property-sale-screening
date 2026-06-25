output "alb_dns_name" {
  description = "ALB の DNS 名（Vercel 環境変数 NEXT_PUBLIC_API_URL に設定する）"
  value       = module.ecs.alb_dns_name
}

output "ecr_repository_url" {
  description = "ECR リポジトリ URL（GitHub Actions ワークフローで image push に使用）"
  value       = module.ecr.repository_url
}

output "rds_endpoint" {
  description = "RDS エンドポイント（Secrets Manager の DATABASE_URL に含まれる）"
  value       = module.rds.endpoint
  sensitive   = true
}

output "s3_bucket_name" {
  description = "開示文書・レポート保管 S3 バケット名"
  value       = module.s3.bucket_name
}

output "ecs_cluster_name" {
  description = "ECS クラスター名（GitHub Actions の deploy ステップで使用）"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS サービス名（GitHub Actions の update-service で使用）"
  value       = module.ecs.service_name
}

output "github_actions_role_arn" {
  description = "GitHub Actions が AssumeRole する IAM ロール ARN（GitHub Secrets に登録する）"
  value       = aws_iam_role.github_actions_deploy.arn
}

output "db_secret_arn" {
  description = "DB 接続情報の Secrets Manager ARN（ECS タスク環境変数として使用）"
  value       = module.rds.db_secret_arn
  sensitive   = true
}
