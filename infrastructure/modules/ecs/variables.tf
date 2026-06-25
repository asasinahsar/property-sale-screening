variable "project_name" {
  description = "プロジェクト名"
  type        = string
}

variable "environment" {
  description = "環境名"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "パブリックサブネット ID リスト（ALB 配置）"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "プライベートサブネット ID リスト（ECS タスク配置）"
  type        = list(string)
}

variable "ecr_repository_url" {
  description = "ECR リポジトリ URL"
  type        = string
}

variable "image_tag" {
  description = "デプロイする Docker イメージのタグ（CD パイプラインが git SHA を注入）"
  type        = string
  default     = "latest"
}

variable "cpu" {
  description = "ECS タスクの CPU ユニット"
  type        = number
}

variable "memory" {
  description = "ECS タスクのメモリ（MB）"
  type        = number
}

variable "db_secret_arn" {
  description = "DB 接続情報 Secrets Manager ARN"
  type        = string
}

variable "s3_bucket_name" {
  description = "開示文書保管 S3 バケット名"
  type        = string
}

variable "aws_region" {
  description = "AWS リージョン"
  type        = string
}

variable "app_port" {
  description = "FastAPI がリッスンするポート"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "ECS サービスの希望タスク数（Phase1: 最小構成）"
  type        = number
  default     = 1
}

variable "ecs_security_group_id" {
  description = "ECS タスクのセキュリティグループ ID（ルートで作成し循環依存を回避）"
  type        = string
}
