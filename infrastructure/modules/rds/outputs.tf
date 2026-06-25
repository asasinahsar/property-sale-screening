output "endpoint" {
  description = "RDS エンドポイント（Secrets Manager の database_url に含まれる）"
  value       = aws_db_instance.main.address
  sensitive   = true
}

output "db_secret_arn" {
  description = "DB 接続情報 Secrets Manager ARN（ECS タスク定義で参照）"
  value       = aws_secretsmanager_secret.db.arn
}

output "rds_security_group_id" {
  description = "RDS セキュリティグループ ID"
  value       = aws_security_group.rds.id
}
