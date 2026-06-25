provider "aws" {
  region = var.aws_region
}

# ─── VPC ─────────────────────────────────────────────────────────────────────
module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name
  environment  = var.environment
}

# ─── ECR ─────────────────────────────────────────────────────────────────────
module "ecr" {
  source       = "./modules/ecr"
  project_name = var.project_name
  environment  = var.environment
}

# ─── S3（開示文書・レポート保管）────────────────────────────────────────────
module "s3" {
  source       = "./modules/s3"
  project_name = var.project_name
  environment  = var.environment
}

# ─── ECS セキュリティグループ（循環依存回避のためルートで作成）──────────────
# rds モジュールが ecs_sg_id を参照し、ecs モジュールが db_secret_arn を参照するため
# ECS SG をルートで先に定義し、両モジュールに渡す
resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-${var.environment}-ecs-sg"
  description = "ECS Fargate: ALB からのトラフィックのみ許可"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-sg"
    Environment = var.environment
  }
}

# ─── RDS PostgreSQL ───────────────────────────────────────────────────────────
module "rds" {
  source             = "./modules/rds"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_name            = var.db_name
  db_username        = var.db_username
  instance_class     = var.rds_instance_class
  ecs_sg_id          = aws_security_group.ecs.id
}

# ─── ECS Fargate + ALB ───────────────────────────────────────────────────────
module "ecs" {
  source                = "./modules/ecs"
  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecr_repository_url    = module.ecr.repository_url
  image_tag             = var.image_tag
  cpu                   = var.ecs_cpu
  memory                = var.ecs_memory
  db_secret_arn         = module.rds.db_secret_arn
  s3_bucket_name        = module.s3.bucket_name
  aws_region            = var.aws_region
  ecs_security_group_id = aws_security_group.ecs.id
}

# ─── GitHub Actions OIDC IAM ─────────────────────────────────────────────────
# CI/CD が ECR push → ECS deploy を行うための OIDC ロール
# アクセスキーは発行しない（OIDC + 専用 IAM ロール方式）
data "aws_caller_identity" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # GitHub Actions の OIDC プロバイダーサムプリント（2023年以降の値）
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions_deploy" {
  name = "${var.project_name}-${var.environment}-github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          # TODO: GitHub リポジトリ名を設定（例: "repo:your-org/property-sale-screening:*"）
          "token.actions.githubusercontent.com:sub" = "repo:TODO_GITHUB_ORG/TODO_REPO_NAME:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_actions_deploy" {
  name = "deploy-policy"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # ECR へのイメージ push
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
        ]
        Resource = "*"
      },
      {
        # ECS のローリングデプロイ
        Effect = "Allow"
        Action = [
          "ecs:RegisterTaskDefinition",
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeTasks",
          "ecs:ListTasks",
        ]
        Resource = "*"
      },
      {
        # ECS タスク実行ロールの iam:PassRole（タスク定義更新に必要）
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = module.ecs.task_execution_role_arn
      },
    ]
  })
}
