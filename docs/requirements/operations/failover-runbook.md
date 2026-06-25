# フェイルオーバ・冗長化ランブック

対象: 不動産売却スクリーニング（property-sale-screening） / Phase 1（Slice N）

## 概要

本ドキュメントは、ECS・RDS の冗長化・フェイルオーバ戦略を定義します。

**目標**:
- **無停止運用（Zero Downtime）**: 単一コンポーネント障害でもサービス継続
- **自動復旧**: ALB ヘルスチェック + ECS Auto Scaling

---

## アーキテクチャ

### Phase 1（現在）: シングル AZ + ECS 冗長化

```
┌─────────────────────────────────────────────────────┐
│ Application Load Balancer (ALB)                    │
│ - HealthCheck: GET /health (interval: 30s)        │
└──────┬──────────────────────────┬──────────────────┘
       │                          │
   ┌───▼────┐              ┌──────▼──┐
   │ ECS    │              │ ECS    │
   │ Task 1 │              │ Task 2 │
   │(AZ-1)  │              │(AZ-1)  │
   └────────┘              └────────┘
        │                      │
        └──────────┬───────────┘
                   │
            ┌──────▼────────┐
            │  RDS Instance │
            │  (AZ-1 only)  │
            │               │
            │ Multi-AZ: No  │
            │ Backup: 7d    │
            │ PITR: Yes     │
            └────────────────┘
```

**特性**:
- ECS: 複数 AZ に desired_count = 2 タスク配置
- ALB: ヘルスチェック失敗タスク自動切り離し
- RDS: シングル AZ（コスト優先）。PITR で復旧可能
- 自動復旧: ECS Auto Scaling で不健全タスク自動起動

### Phase 2（検討中）: Multi-AZ RDS

```
# Terraform で有効化
TF_VAR_rds_multi_az=true terraform apply

変更内容:
- RDS Primary: AZ-1
- RDS Standby: AZ-2（同期レプリケーション）
- Failover時間: 1-2分（自動）
- RPO: 0（同期レプリケーション）
```

---

## ECS 冗長化・ヘルスチェック

### Terraform 設定

```hcl
# infrastructure/modules/ecs.tf

resource "aws_ecs_service" "app" {
  name               = "property-screening-backend"
  cluster            = aws_ecs_cluster.prod.id
  task_definition    = aws_ecs_task_definition.app.arn
  
  # 冗長化
  desired_count      = 2  # 最小 2 タスク
  
  # 複数 AZ 配置
  network_configuration {
    subnets = [
      aws_subnet.private_az1.id,
      aws_subnet.private_az2.id
    ]
    security_groups = [aws_security_group.ecs.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "fastapi"
    container_port   = 8000
  }
  
  # Auto Scaling
  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 100
  }
}

# ALB ヘルスチェック
resource "aws_lb_target_group" "app" {
  name                 = "property-screening-backend"
  port                 = 8000
  protocol             = "HTTP"
  vpc_id               = aws_vpc.main.id
  
  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30  # 30秒ごとにヘルスチェック
    path                = "/health"
    matcher             = "200"  # HTTP 200 で健全と判定
  }
  
  deregistration_delay = 30  # 切断時のタイムアウト
}

# Auto Scaling ポリシー
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 4
  min_capacity       = 2
  resource_id        = "service/property-screening-prod/property-screening-backend"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  policy_name       = "ecs-cpu-scaling"
  policy_type       = "TargetTrackingScaling"
  resource_id       = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0  # CPU >= 70% で +1 タスク
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_down_cooldown = 300  # 5分間は scale down 抑制
  }
}
```

### ヘルスチェックエンドポイント実装

```python
# backend/app/main.py

from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """
    ALB ヘルスチェック用エンドポイント
    
    返値: {"status": "ok"} (HTTP 200)
    """
    # DB 接続確認
    try:
        async with get_db() as session:
            await session.execute("SELECT 1")
    except Exception as e:
        return {"status": "error", "message": str(e)}, 503
    
    return {"status": "ok"}
```

---

## 自動フェイルオーバ（ECS）

### シナリオ: Task 1 が障害状態

**タイムライン**:

| 時刻 | イベント | 状態 |
|------|---------|------|
| 00:00 | Task 1 クラッシュ | desired=2, running=1 |
| 00:00-00:30 | ALB ヘルスチェック失敗（2回連続） | target group から切り離し |
| 00:30-01:00 | ALB が Task 2 のみにトラフィック振分 | サービス継続 |
| 01:00 | ECS Auto Scaling 検出 | 新規 Task 3 起動 |
| 02:00 | Task 3 起動完了・ヘルスチェック通過 | desired=2, running=2 |

**ユーザーの体感**:
- ダウンタイム: 0 秒
- レイテンシ上昇: 一時的に +5-10ms（1タスク負荷増）
- エラー: なし

### 手動検証（テスト）

**準備**:
```bash
# 本番環境でテスト実施（負荷が低い時間帯、22:00-23:00 推奨）
aws ecs list-tasks \
  --cluster property-screening-prod \
  --service-name property-screening-backend \
  --query 'taskArns' \
  --output text

# 例: arn:aws:ecs:us-east-1:xxx:task/property-screening-prod/abc123
# arn:aws:ecs:us-east-1:xxx:task/property-screening-prod/def456
```

**テスト手順**:

1. **Task を意図的に停止**
   ```bash
   aws ecs stop-task \
     --cluster property-screening-prod \
     --task arn:aws:ecs:us-east-1:xxx:task/property-screening-prod/abc123 \
     --reason "Manual failover test"
   ```

2. **CloudWatch メトリクス監視**
   - ECS Task Count: desired=2, running=1 → 1 → 2
   - ALB Target Health: unhealthy=1 → 0
   - HTTP Errors: 0 （エラーなし）

3. **API テスト**
   ```bash
   # ループでリクエスト送信、エラーなし確認
   for i in {1..100}; do
     curl -X GET https://api.example.com/health
     sleep 1
   done
   ```

4. **ログ確認**
   ```bash
   aws logs tail /aws/ecs/property-screening-backend \
     --since 5m --follow
   
   # "Task stopped" ログが見えるはず
   ```

---

## RDS Multi-AZ フェイルオーバ（Phase 2）

### 有効化手順

```bash
# 環境変数で有効化
export TF_VAR_rds_multi_az=true

# Terraform apply（ダウンタイム: 数分）
cd infrastructure
terraform apply -var-file=prod.tfvars

# 完了確認
aws rds describe-db-instances \
  --db-instance-identifier property-screening-prod-db \
  --query 'DBInstances[0].MultiAZ'
```

### Terraform 定義

```hcl
# infrastructure/variables.tf
variable "rds_multi_az" {
  type        = bool
  description = "Enable Multi-AZ for RDS (Phase 2)"
  default     = false  # Phase 1: disabled
}

# infrastructure/modules/rds.tf
resource "aws_db_instance" "postgres" {
  # ...
  multi_az = var.rds_multi_az
  
  # Multi-AZ 有効時の自動フェイルオーバ
  # AWS が Primary → Standby に自動切替（1-2分）
}
```

### Failover テスト（有効化後）

```bash
# Standby への自動フェイルオーバ テスト
aws rds reboot-db-instance \
  --db-instance-identifier property-screening-prod-db \
  --force-failover  # Standby へのフェイルオーバ強制

# 進捗監視
aws rds describe-db-instances \
  --db-instance-identifier property-screening-prod-db \
  --query 'DBInstances[0].DBInstanceStatus'

# "rebooting" → "available" （1-2分で完了）
```

---

## CloudWatch Alarm - 監視

### ALB Target Unhealthy

```hcl
# infrastructure/modules/monitoring.tf

resource "aws_cloudwatch_metric_alarm" "alb_target_unhealthy" {
  alarm_name          = "ALB-Target-Unhealthy"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0.5  # 1台以上が unhealthy
  
  alarm_actions = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.app.arn_suffix
  }
}
```

### ECS Service Desired Count と Running Count の乖離

```hcl
resource "aws_cloudwatch_metric_alarm" "ecs_task_mismatch" {
  alarm_name          = "ECS-Task-Count-Mismatch"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5  # 5分連続
  metric_name         = "DesiredTaskCount"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 2.5  # desired > running
  
  alarm_actions = [aws_sns_topic.alarms.arn]
}
```

---

## 冗長化テストスケジュール

| タイミング | テスト内容 | 所要時間 | 備考 |
|----------|----------|--------|------|
| Slice N 完成時 | ECS ヘルスチェック・自動復旧 | 10分 | Sprint 3 デモ証跡として提示 |
| 毎月初（深夜） | Task 強制停止テスト | 5分 | 本番環境で無停止確認 |
| 4 半期ごと | RDS Multi-AZ failover テスト | 10分 | Phase 2 前に dry-run |

---

## チェックリスト

### ECS 冗長化（Phase 1）

- [ ] Terraform で desired_count = 2 設定
- [ ] ALB ヘルスチェックパス `/health` 実装
- [ ] `/health` が HTTP 200 返却確認
- [ ] Auto Scaling ポリシー設定（CPU >= 70%）
- [ ] Task 強制停止テスト実施（自動復旧確認）
- [ ] CloudWatch メトリクス確認（エラーなし）
- [ ] Slack アラーム設定確認

### RDS Multi-AZ（Phase 2 検討）

- [ ] TF_VAR_rds_multi_az テスト設定
- [ ] Terraform plan で Multi-AZ 変更確認
- [ ] ダウンタイム見積（数分）
- [ ] Failover テスト実施（Standby 切替）
- [ ] RPO=0 確認（同期レプリケーション）

---

## 参考

- AWS ECS Auto Scaling: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html
- ALB Target Health: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-health-checks.html
- RDS Multi-AZ: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html
