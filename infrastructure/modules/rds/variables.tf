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

variable "private_subnet_ids" {
  description = "プライベートサブネット ID リスト（DB Subnet Group に 2 AZ 必要）"
  type        = list(string)
}

variable "instance_class" {
  description = "RDS インスタンスタイプ"
  type        = string
}

variable "db_name" {
  description = "データベース名"
  type        = string
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
}

variable "ecs_sg_id" {
  description = "ECS タスクのセキュリティグループ ID（RDS へのアクセスを許可）"
  type        = string
}

variable "postgres_version" {
  description = "PostgreSQL バージョン"
  type        = string
  default     = "15"
}

variable "allocated_storage" {
  description = "ストレージ容量（GB）"
  type        = number
  default     = 20 # TODO: 本番運用量に応じて変更（最低 20GB 推奨）
}

variable "backup_retention_days" {
  description = "バックアップ保持日数"
  type        = number
  default     = 7
}
