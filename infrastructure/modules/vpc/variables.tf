variable "project_name" {
  description = "プロジェクト名（リソース命名プレフィックス）"
  type        = string
}

variable "environment" {
  description = "環境名"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR ブロック"
  type        = string
  default     = "10.0.0.0/16" # drawio から読み取った値
}

# Phase1: シングルAZ構成。ただし ALB は 2 AZ が必須のため public subnet は 2 つ作成する
variable "public_subnet_cidrs" {
  description = "パブリックサブネット CIDR（ALB 用。2 AZ 必須）"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"] # TODO: 必要に応じて変更
}

variable "private_subnet_cidrs" {
  description = "プライベートサブネット CIDR（ECS + RDS 用。RDS subnet group に 2 AZ 必要）"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"] # TODO: 必要に応じて変更
}

variable "availability_zones" {
  description = "使用する AZ（最低 2 つ必要: ALB と RDS の要件）"
  type        = list(string)
  default     = ["ap-northeast-1a", "ap-northeast-1c"] # TODO: リージョンに応じて変更
}
