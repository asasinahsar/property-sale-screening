terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # backend は infrastructure/backend.tf.example を参照
  # TODO をすべて埋めて backend.tf にコピーした後、terraform init を実行する
  backend "s3" {}
}

# ルートモジュールを呼び出す
module "root" {
  source = "../../"

  project_name       = var.project_name
  aws_region         = var.aws_region
  environment        = var.environment
  image_tag          = var.image_tag
  ecs_cpu            = var.ecs_cpu
  ecs_memory         = var.ecs_memory
  rds_instance_class = var.rds_instance_class
  db_name            = var.db_name
  db_username        = var.db_username
}

# ─── 変数（terraform.tfvars から注入）────────────────────────────────────────
variable "project_name" { type = string }
variable "aws_region" { type = string }
variable "environment" { type = string }
variable "image_tag" {
  type    = string
  default = "latest"
}
variable "ecs_cpu" { type = number }
variable "ecs_memory" { type = number }
variable "rds_instance_class" { type = string }
variable "db_name" { type = string }
variable "db_username" { type = string }
