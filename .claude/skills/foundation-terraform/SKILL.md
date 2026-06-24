---
name: foundation-terraform
description: docs/requirements/ の drawio・ドキュメントを読み、Terraform ファイルを生成する。値の埋め方を案内する
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Slice 0-7: Terraform AWS IaC 構築

`docs/requirements/` に含まれる drawio・operation ドキュメントからアーキテクチャを読み取り、
Terraform のスケルトンを生成するスキル。**具体的な名前・数値はユーザーが埋める。**

## Purpose

1. `docs/requirements/` の drawio・ドキュメントを読んでアーキテクチャを把握する
2. 把握した内容から Terraform のモジュール構成を決定する
3. ファイルを生成し、**ユーザーが埋めるべき箇所を `# TODO:` コメントで明示する**
4. 何をどこに書けばよいかを一覧で案内する

## When to use

- Slice 0-6（foundation-api-integration）完了後に実行
- AWS への本番デプロイを計画している

## Prerequisites

- Terraform（>= 1.6）がインストールされていること（`terraform version` で確認）
- AWS CLI がインストールされ、認証情報が設定されていること（`aws sts get-caller-identity` で確認）
- `docs/requirements/` に drawio ファイルまたは operation ドキュメントが存在すること

## Outputs

```
infrastructure/
├── backend.tf.example            # ← S3 backend 設定の雛形（TODO を埋めて backend.tf にコピー）
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/                      # カスタムモジュール（公式モジュール選択時は不要）
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecr/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── rds/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/
    │   ├── main.tf
    │   └── terraform.tfvars      # ← ユーザーが値を記入するファイル
    └── prod/                     # drawio に prod 環境が存在する場合のみ作成
        ├── main.tf
        └── terraform.tfvars
```

## Procedure

### Step 1: docs/requirements/ を読む

```bash
ls docs/requirements/ 2>/dev/null || echo "docs/requirements/ が存在しません"
```

drawio ファイルと operation 系ドキュメントを列挙する：

```bash
find docs/requirements/ -name "*.drawio" -o -name "operation*.md" -o -name "infrastructure*.md" 2>/dev/null
```

存在するファイルを **すべて Read** する。
drawio は XML なので、以下の要素を探して読み取る：

- どの AWS サービスが登場するか（ECS / RDS / VPC / ALB / CloudFront / S3 / Lambda など）
- サービス間の接続（矢印・グルーピング）
- 環境の分割（dev / prod / staging など）
- Public / Private サブネットの有無
- 外部サービス連携（Vercel / Sentry / Slack など）

### Step 2: 読み取った内容を整理してユーザーに共有する

以下の形式でユーザーに提示する：

```
## docs/requirements/ から読み取った内容

### 登場する AWS サービス
- （例）VPC, ALB, ECS Fargate, RDS PostgreSQL, ECR, Secrets Manager

### ネットワーク構成
- （例）Public サブネット × 2 AZ、Private サブネット × 2 AZ

### 環境
- （例）dev, prod

### 確認できなかった・ドキュメントに記載のない項目
- （例）RDS インスタンスタイプ、ECS CPU/メモリ、S3 バケット名

この内容をもとに Terraform のスケルトンを生成します。
不足している情報は生成ファイル内に TODO コメントとして残します。
```

### Step 3: モジュール方式をユーザーに選ばせる

以下をユーザーに提示し、方式を決めてもらう：

```
## Terraform モジュール方式を選んでください

A) カスタムモジュール（modules/ 配下に自作）
   - VPC・ECS・RDS の内部実装が全て見える
   - 学習コスト高・カスタマイズ自由度高
   - Sprint 3 の学習目的に適している

B) 公式モジュール（Terraform Registry）
   - terraform-aws-modules/vpc/aws
   - terraform-aws-modules/ecs/aws
   - terraform-aws-modules/rds/aws
   などを利用
   - 実装コスト低・内部は抽象化
   - 本番プロジェクトでよく使われる構成

どちらにしますか？（A / B）
```

**A を選択した場合**: Step 4 以降でカスタムモジュールを生成する
**B を選択した場合**: Step 4 以降で公式モジュールの呼び出しコードを生成する（`modules/` ディレクトリは作らない）

### Step 4: backend.tf.example を生成する

> **`backend.tf` ではなく `backend.tf.example` として生成する。**
> S3 バケット名などの TODO が残ったまま `terraform init` が実行されると設定が壊れるため、
> ユーザーが値を埋めてから `cp backend.tf.example backend.tf` するフローにする。

```hcl
# infrastructure/backend.tf.example
# ─────────────────────────────────────────────────────────────
# 使い方:
#   1. このファイルの TODO をすべて埋める
#   2. cp backend.tf.example backend.tf
#   3. terraform init を実行する
# ─────────────────────────────────────────────────────────────
terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "TODO: Terraform State を保存する S3 バケット名（例: myproject-terraform-state）"
    key            = "terraform.tfstate"
    region         = "TODO: AWS リージョン（例: ap-northeast-1）"
    dynamodb_table = "TODO: ロック用 DynamoDB テーブル名（例: myproject-terraform-lock）"
    encrypt        = true
  }
}
```

`.gitignore` に `backend.tf` を追記して、誤コミットを防ぐことをユーザーに案内する：

```
# .gitignore に追加
infrastructure/backend.tf
```

### Step 5: variables.tf を生成する

`image_tag` 変数を追加する。**ECS タスク定義で `:latest` は使わない**。
デプロイ時（CD パイプライン）に `TF_VAR_image_tag=<git-sha>` で上書きする想定。

```hcl
# infrastructure/variables.tf

variable "project_name" {
  description = "プロジェクト名（リソース命名プレフィックス）"
  type        = string
  default     = "TODO: プロジェクト名を入力（例: myproject）"
}

variable "aws_region" {
  description = "AWS リージョン"
  type        = string
  default     = "TODO: リージョンを入力（例: ap-northeast-1）"
}

variable "environment" {
  description = "環境名"
  type        = string
  # environments/dev/terraform.tfvars で上書き
}

variable "image_tag" {
  description = "デプロイする Docker イメージのタグ（CD パイプラインが git SHA を注入する）"
  type        = string
  default     = "latest" # ローカル開発時のフォールバック。本番 CD では TF_VAR_image_tag で上書き
}

variable "ecs_cpu" {
  description = "ECS タスクの CPU ユニット数（256 / 512 / 1024 / 2048）"
  type        = number
  default     = 0 # TODO: CPU を入力（開発用途なら 256 推奨）
}

variable "ecs_memory" {
  description = "ECS タスクのメモリ（MB）（512 / 1024 / 2048 / 4096）"
  type        = number
  default     = 0 # TODO: メモリを入力（256cpu なら 512 推奨）
}

variable "rds_instance_class" {
  description = "RDS インスタンスタイプ"
  type        = string
  default     = "TODO: インスタンスタイプを入力（例: db.t3.micro）"
}

variable "db_name" {
  description = "データベース名"
  type        = string
  default     = "TODO: DB 名を入力（例: app_db）"
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
  default     = "TODO: DB ユーザー名を入力（例: appuser）"
}
```

### Step 6: main.tf を生成する

Step 3 でユーザーが選んだ方式に応じて、以下のどちらかを生成する。

---

**A: カスタムモジュール方式**

```hcl
# infrastructure/main.tf
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name
  environment  = var.environment
}

module "ecr" {
  source       = "./modules/ecr"
  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source             = "./modules/rds"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_name            = var.db_name
  db_username        = var.db_username
  instance_class     = var.rds_instance_class
}

module "ecs" {
  source             = "./modules/ecs"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  ecr_repository_url = module.ecr.repository_url
  image_tag          = var.image_tag
  cpu                = var.ecs_cpu
  memory             = var.ecs_memory
  db_endpoint        = module.rds.endpoint
}
```

---

**B: 公式モジュール方式**

```hcl
# infrastructure/main.tf
provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" { state = "available" }

# VPC: terraform-aws-modules/vpc/aws
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-${var.environment}"
  cidr = "TODO: VPC CIDR（例: 10.0.0.0/16）"

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnets  = ["TODO: public subnet CIDR 1", "TODO: public subnet CIDR 2"]
  private_subnets = ["TODO: private subnet CIDR 1", "TODO: private subnet CIDR 2"]

  enable_nat_gateway = true
  single_nat_gateway = true # コスト削減。本番では false にする

  tags = { Environment = var.environment }
}

# ECR（公式モジュールなし → aws_ecr_repository リソースを直接定義）
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-${var.environment}-backend"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

# RDS: terraform-aws-modules/rds/aws
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-${var.environment}-db"

  engine         = "postgres"
  engine_version = "15"
  instance_class = var.rds_instance_class

  db_name  = var.db_name
  username = var.db_username
  # パスワードは自動生成（manage_master_user_password = true）
  manage_master_user_password = true

  vpc_security_group_ids = [module.security_group_rds.security_group_id]
  subnet_ids             = module.vpc.private_subnets
  create_db_subnet_group = true

  skip_final_snapshot = true
  deletion_protection = false

  tags = { Environment = var.environment }
}

# ECS: terraform-aws-modules/ecs/aws
module "ecs" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 5.0"

  cluster_name = "${var.project_name}-${var.environment}-cluster"

  services = {
    backend = {
      cpu    = var.ecs_cpu
      memory = var.ecs_memory

      container_definitions = {
        backend = {
          image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
          essential = true
          port_mappings = [{
            container_port = 8000
            protocol       = "tcp"
          }]
          environment = [
            # TODO: terraform apply 後に RDS エンドポイントを確認して DATABASE_URL を設定する
            # { name = "DATABASE_URL", value = "postgresql+asyncpg://..." }
          ]
        }
      }

      load_balancer = {
        service = {
          target_group_arn = module.alb.target_groups["backend"].arn
          container_name   = "backend"
          container_port   = 8000
        }
      }

      subnet_ids         = module.vpc.private_subnets
      assign_public_ip   = false
    }
  }

  tags = { Environment = var.environment }
}

# ALB（公式モジュール）
module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name    = "${var.project_name}-${var.environment}-alb"
  vpc_id  = module.vpc.vpc_id
  subnets = module.vpc.public_subnets

  target_groups = {
    backend = {
      name             = "${var.project_name}-${var.environment}-tg"
      protocol         = "HTTP"
      port             = 8000
      target_type      = "ip"
      health_check     = { path = "/api/v1/health" }
    }
  }

  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"
      forward  = { target_group_key = "backend" }
    }
  }

  tags = { Environment = var.environment }
}

# セキュリティグループ（RDS 用）
module "security_group_rds" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name   = "${var.project_name}-${var.environment}-rds-sg"
  vpc_id = module.vpc.vpc_id

  ingress_with_cidr_blocks = [{
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = module.vpc.vpc_cidr_block
  }]
}
```

---

### Step 7: outputs.tf を生成する（A・B 共通）

```hcl
# infrastructure/outputs.tf
output "alb_dns_name" {
  description = "ALB の DNS 名（Frontend / CD パイプラインで使用）"
  value       = try(module.ecs.alb_dns_name, module.alb.dns_name, "")
}

output "ecr_repository_url" {
  description = "ECR リポジトリ URL（CD パイプラインで image_tag と組み合わせて使用）"
  value       = try(module.ecr.repository_url, aws_ecr_repository.backend.repository_url, "")
}

output "rds_endpoint" {
  description = "RDS エンドポイント（Backend の DATABASE_URL に使用）"
  value       = try(module.rds.db_instance_endpoint, module.rds.endpoint, "")
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS クラスター名（CD パイプラインで update-service に使用）"
  value       = try(module.ecs.cluster_name, "")
}

output "ecs_service_name" {
  description = "ECS サービス名（CD パイプラインで update-service に使用）"
  value       = try(module.ecs.services["backend"].name, "")
}
```

### Step 8: モジュールのスケルトンを生成する（A 選択時のみ）

B（公式モジュール）を選択した場合はこの Step をスキップする。

各モジュールは **構造のみ生成**し、サイジング・ネットワーク CIDR などは `# TODO:` にする。

以下を各モジュールに生成する（vpc / ecr / ecs / rds）：
- `main.tf` — リソース定義（具体的な値は TODO）
- `variables.tf` — 入力変数（型・description を記載）
- `outputs.tf` — 出力値（下流モジュールが必要とするもの）

**ecs/main.tf の image_tag 部分（A 方式）:**

```hcl
# modules/ecs/main.tf（抜粋）
resource "aws_ecs_task_definition" "backend" {
  cpu    = var.cpu
  memory = var.memory

  container_definitions = jsonencode([{
    name  = "backend"
    # image_tag は CD パイプラインが TF_VAR_image_tag=<git-sha> で注入する
    # ローカル開発時のみ "latest" にフォールバック
    image = "${var.ecr_repository_url}:${var.image_tag}"
    port_mappings = [{
      container_port = 8000
      protocol       = "tcp"
    }]
    environment = [
      # TODO: terraform apply 後に RDS エンドポイントで置き換える
      # { name = "DATABASE_URL", value = "postgresql+asyncpg://..." }
    ]
    # ...
  }])
}
```

**modules/ecs/variables.tf に image_tag を追加する:**

```hcl
variable "image_tag" {
  description = "デプロイする Docker イメージのタグ（CD パイプラインが注入）"
  type        = string
  default     = "latest"
}
```

### Step 9: environments/dev/terraform.tfvars を生成する

**このファイルがユーザーの主な記入場所**。全項目に TODO コメントを入れる。

```hcl
# environments/dev/terraform.tfvars
# ─────────────────────────────────────────────
# ここに具体的な値を入力してください
# ─────────────────────────────────────────────

environment        = "dev"

# 1. プロジェクト名（リソース命名プレフィックスになります）
#    例: "myproject" → ECS クラスター名は "myproject-dev-cluster"
project_name       = "TODO"

# 2. AWS リージョン
#    例: "ap-northeast-1"（東京）
aws_region         = "TODO"

# 3. ECS CPU（単位: CPU ユニット）
#    選択肢: 256 / 512 / 1024 / 2048
#    開発用途なら 256 推奨
ecs_cpu            = 0 # TODO

# 4. ECS メモリ（単位: MB）
#    CPU に対応した選択肢: 256→512, 512→1024, 1024→2048
ecs_memory         = 0 # TODO

# 5. RDS インスタンスタイプ
#    例: "db.t3.micro"（開発用途推奨）
rds_instance_class = "TODO"

# 6. データベース名
db_name            = "TODO"

# 7. データベースユーザー名
db_username        = "TODO"

# image_tag はデプロイ時に CD パイプラインが上書きする
# ローカル動作確認のみ手動で指定する（通常は設定不要）
# image_tag = "latest"
```

### Step 10: backend.tf.example の使い方と事前 AWS リソース作成手順を案内する

```
## terraform init の前に必要な作業

### 1. backend.tf.example の TODO をすべて埋める

backend.tf.example を開き、TODO を書き換えてください：
- bucket: Terraform State 用 S3 バケット名
- region: AWS リージョン
- dynamodb_table: ロック用 DynamoDB テーブル名

### 2. backend.tf にコピーする（Git 管理外）

cp infrastructure/backend.tf.example infrastructure/backend.tf

backend.tf は .gitignore で除外されているため、リポジトリにコミットされません。
各開発者・CI がそれぞれ backend.tf を用意する運用になります。

### 3. S3 バケットと DynamoDB テーブルを作成する

aws s3 mb s3://{バケット名} --region {リージョン}
aws s3api put-bucket-versioning \
  --bucket {バケット名} \
  --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name {テーブル名} \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

### 4. terraform init を実行する

cd infrastructure
terraform init
```

### Step 11: TODO 一覧をユーザーに提示する

生成が完了したら、以下の形式でユーザーに案内する：

```
## 生成完了。次に埋めるべき TODO 一覧

### まず埋める（terraform init に必要）
| ファイル | 項目 | 説明 |
|---------|------|------|
| backend.tf.example | bucket | Terraform State 用 S3 バケット名 |
| backend.tf.example | region | AWS リージョン |
| backend.tf.example | dynamodb_table | ロック用 DynamoDB テーブル名 |

→ 埋めたら: cp infrastructure/backend.tf.example infrastructure/backend.tf

### 次に埋める（terraform apply に必要）
| ファイル | 項目 | 説明 |
|---------|------|------|
| environments/dev/terraform.tfvars | project_name | プロジェクト名（命名プレフィックス） |
| environments/dev/terraform.tfvars | aws_region | AWS リージョン |
| environments/dev/terraform.tfvars | ecs_cpu | ECS CPU（256/512/1024/2048） |
| environments/dev/terraform.tfvars | ecs_memory | ECS メモリ（MB） |
| environments/dev/terraform.tfvars | rds_instance_class | RDS インスタンスタイプ |
| environments/dev/terraform.tfvars | db_name | データベース名 |
| environments/dev/terraform.tfvars | db_username | データベースユーザー名 |
| main.tf（公式モジュール選択時） | VPC CIDR / Subnet CIDR | ネットワーク設計値 |
| modules/vpc/main.tf（カスタム選択時） | cidr_block | VPC・サブネット CIDR |

### 後から埋める（terraform apply 後・CD 設定時）
| 項目 | 説明 |
|------|------|
| DATABASE_URL（ECS 環境変数） | terraform output rds_endpoint で確認後に設定 |
| image_tag | CD パイプラインが TF_VAR_image_tag=<git-sha> で自動注入する |

### docs/requirements/ から読み取れなかった項目（要確認）
（Step 2 で「確認できなかった項目」として挙げたものを再掲）
```

### Step 12: terraform validate を実行する

TODO が残っていても validate は構文チェックのみなので実行できる：

```bash
cd infrastructure
terraform init -backend=false
terraform validate
```

validate が通れば構造は正しい。

## チェックリスト

- [ ] `docs/requirements/` の drawio・ドキュメントをすべて Read した
- [ ] 読み取った内容をユーザーに共有した
- [ ] カスタムモジュール / 公式モジュールどちらかをユーザーが選択した
- [ ] `backend.tf.example` を生成した（`backend.tf` は生成していない）
- [ ] `.gitignore` に `infrastructure/backend.tf` を追記した
- [ ] `variables.tf` に `image_tag` 変数が含まれている
- [ ] ECS タスク定義の image が `:latest` 固定ではなく `var.image_tag` になっている
- [ ] `environments/dev/terraform.tfvars` に全 TODO が記載されている
- [ ] `terraform init` 前の作業手順（S3・DynamoDB 作成・cp）を案内した
- [ ] TODO 一覧をユーザーに提示した
- [ ] `terraform validate` が成功した（構文エラーなし）

## 注意事項

- **`backend.tf` は生成しない**: `backend.tf.example` のみ生成し、ユーザーが cp してから使う。誤った設定で `terraform init` されることを防ぐ
- **`:latest` を使わない**: ECS の image タグは `var.image_tag` 経由にする。CD パイプラインが git SHA を `TF_VAR_image_tag` で注入する想定
- **値は書かない**: 具体的な名前・数値・ARN はすべて `# TODO:` にする。推奨値はコメントで示す
- **構造は drawio から**: モジュール追加・削除の判断は drawio ベースで行う。drawio にないサービスは追加しない
- **DB パスワードは自動生成**: カスタムモジュール方式では `random_password`、公式モジュール方式では `manage_master_user_password = true` を使う。ユーザーに入力させない
