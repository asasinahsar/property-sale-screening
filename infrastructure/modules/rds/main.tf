# DB パスワードを自動生成（ハードコード禁止）
resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}:?"
}

# DB 接続情報を Secrets Manager に保管
resource "aws_secretsmanager_secret" "db" {
  name                    = "${var.project_name}-${var.environment}-db-credentials"
  description             = "RDS PostgreSQL 接続情報"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-credentials"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    # terraform apply 後に endpoint が確定してから DATABASE_URL を更新する
    # TODO: apply 完了後に以下の DATABASE_URL を実際の endpoint に更新すること
    engine   = "postgres"
    host     = aws_db_instance.main.address
    port     = 5432
    dbname   = var.db_name
    # DATABASE_URL 形式（FastAPI / SQLAlchemy asyncpg 用）
    database_url = "postgresql+asyncpg://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.address}:5432/${var.db_name}"
  })
}

# RDS セキュリティグループ（ECS からのみ 5432 を許可）
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "RDS へのアクセスを ECS タスクのみに制限"
  vpc_id      = var.vpc_id

  ingress {
    description     = "ECS Fargate からの PostgreSQL アクセス"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

# DB Subnet Group（2 AZ 必須）
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

# RDS PostgreSQL インスタンス
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine         = "postgres"
  engine_version = var.postgres_version
  instance_class = var.instance_class

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  allocated_storage     = var.allocated_storage
  storage_type          = "gp2"
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false # プライベートサブネットに隔離

  backup_retention_period = var.backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Phase1: コスト優先のため無効化（Phase2 で有効化を検討）
  multi_az = false

  # デモ環境のため削除保護は無効（本番運用に移行する場合は true にすること）
  deletion_protection = false
  skip_final_snapshot = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Environment = var.environment
  }
}
