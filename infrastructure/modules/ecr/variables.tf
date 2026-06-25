variable "project_name" {
  description = "プロジェクト名"
  type        = string
}

variable "environment" {
  description = "環境名"
  type        = string
}

variable "image_tag_mutability" {
  description = "イメージタグの変更可否（MUTABLE / IMMUTABLE）"
  type        = string
  default     = "MUTABLE"
}

variable "lifecycle_policy_count" {
  description = "保持するイメージ数（古いイメージを自動削除）"
  type        = number
  default     = 10
}
