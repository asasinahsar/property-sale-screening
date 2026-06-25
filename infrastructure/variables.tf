variable "project_name" {
  description = "プロジェクト名（リソース命名プレフィックス）"
  type        = string
  default     = "TODO: プロジェクト名を入力（例: prop-screening）"
}

variable "aws_region" {
  description = "AWS リージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "環境名（prod / dev）"
  type        = string
}

variable "image_tag" {
  description = "デプロイする Docker イメージのタグ（CD パイプラインが git SHA を TF_VAR_image_tag で注入する）"
  type        = string
  default     = "latest" # ローカル動作確認時のフォールバック。本番 CD では上書き
}

variable "ecs_cpu" {
  description = "ECS タスクの CPU ユニット（256 / 512 / 1024 / 2048）"
  type        = number
  default     = 256 # TODO: 適切な値を設定（低トラフィック用途なら 256 推奨）
}

variable "ecs_memory" {
  description = "ECS タスクのメモリ（MB）（cpu=256 なら 512 推奨）"
  type        = number
  default     = 512 # TODO: 適切な値を設定
}

variable "rds_instance_class" {
  description = "RDS インスタンスタイプ"
  type        = string
  default     = "db.t3.micro" # TODO: 適切な値を設定（開発・デモ用途なら db.t3.micro 推奨）
}

variable "db_name" {
  description = "データベース名"
  type        = string
  default     = "TODO: DB 名を入力（例: prop_screening）"
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
  default     = "TODO: DB ユーザー名を入力（例: appuser）"
}
