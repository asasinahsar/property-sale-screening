output "alb_dns_name" {
  description = "ALB の DNS 名（Vercel 環境変数 NEXT_PUBLIC_API_URL に設定する）"
  value       = aws_lb.main.dns_name
}

output "cluster_name" {
  description = "ECS クラスター名（GitHub Actions の deploy ステップで使用）"
  value       = aws_ecs_cluster.main.name
}

output "service_name" {
  description = "ECS サービス名（GitHub Actions の update-service で使用）"
  value       = aws_ecs_service.backend.name
}

output "ecs_security_group_id" {
  description = "ECS タスクのセキュリティグループ ID（ルートから渡された値をそのまま出力）"
  value       = var.ecs_security_group_id
}

output "task_execution_role_arn" {
  description = "ECS タスク実行ロール ARN（GitHub Actions の IAM PassRole で使用）"
  value       = aws_iam_role.task_execution.arn
}
