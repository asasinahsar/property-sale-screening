# 復旧手順書（Restore Runbook）

対象: 不動産売却スクリーニング（property-sale-screening） / Phase 1

## クイックリファレンス

| 障害 | RTO | RPO | 手順 |
|------|-----|-----|------|
| RDS ディスク満杯 | 10分 | 0分 | ストレージ拡張（Terraform） |
| RDS インスタンスクラッシュ | 15分 | 1分以内 | Terraform replace + PITR |
| データベーススキーマ破損 | 30分 | 24時間 | PITR で復旧インスタンス起動→復元 |
| S3 オブジェクト誤削除 | 5分 | 即座 | S3 versioning から復元 |
| ECS タスク障害 | 1分 | 0分 | ALB が自動切り離し・ECS 再起動 |
| ALB 障害 | 30分 | 0分 | Terraform replace |

---

## 詳細手順

### Case 1: RDS インスタンス障害（クラッシュ）

**症状**: `POST /api/screenings` が 503 を返す、データベース接続エラーログ

**復旧手順**:

1. **現状確認**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier property-screening-prod-db \
     --query 'DBInstances[0].DBInstanceStatus'
   ```
   
   - `creating` / `available` → 正常
   - `failed` / `incompatible-credentials` → 障害

2. **復旧（方法 A: 再起動）**
   ```bash
   # インスタンス再起動（30秒～2分のダウンタイム）
   aws rds reboot-db-instance \
     --db-instance-identifier property-screening-prod-db
   
   # 復旧待機
   aws rds wait db-instance-available \
     --db-instance-identifier property-screening-prod-db
   ```

3. **復旧（方法 B: PITR で新規作成）** - 再起動が失敗した場合
   
   `backup-runbook.md` の「シナリオ 1: データベース全体の復旧」を参照
   
   - RTO: 30分
   - RPO: 24時間以内

4. **確認**
   ```bash
   # ヘルスチェック API を実行
   curl -X GET https://api.example.com/health
   
   # CloudWatch Logs でエラーなし
   aws logs tail /aws/rds/instance/property-screening-prod-db/error
   ```

---

### Case 2: S3 オブジェクト誤削除

**症状**: 「ファイルが見つかりません」エラー、`GET /api/files/{id}` が 404

**復旧手順**:

1. **バージョン一覧確認**
   ```bash
   aws s3api list-object-versions \
     --bucket property-screening-generated-files \
     --prefix "reports/company-123.pdf" \
     --query 'Versions[].[Key,VersionId,LastModified,IsLatest]' \
     --output table
   ```

2. **旧バージョンから復元**
   ```bash
   # 削除対象前のバージョンをコピー
   aws s3api copy-object \
     --copy-source property-screening-generated-files/reports/company-123.pdf?versionId=abc123def456 \
     --bucket property-screening-generated-files \
     --key reports/company-123.pdf
   
   # または、旧バージョンを新ファイルとして復元
   aws s3api get-object \
     --bucket property-screening-generated-files \
     --key reports/company-123.pdf \
     --version-id abc123def456 \
     company-123-restored.pdf
   ```

3. **確認**
   ```bash
   aws s3 ls s3://property-screening-generated-files/reports/company-123.pdf
   ```

---

### Case 3: ECS タスク障害

**症状**: ALB ヘルスチェック失敗、`GET /health` が 5xx

**復旧手順**:

1. **現状確認（自動修復が走ったか）**
   ```bash
   # ECS タスク一覧確認
   aws ecs list-tasks \
     --cluster property-screening-prod \
     --service-name property-screening-backend \
     --query 'taskArns'
   
   # タスク詳細確認
   aws ecs describe-tasks \
     --cluster property-screening-prod \
     --tasks arn:aws:ecs:us-east-1:xxx:task/property-screening-prod/... \
     --query 'tasks[0].{LastStatus:lastStatus,HealthStatus:healthStatus}'
   ```

2. **手動再起動（自動修復が失敗した場合）**
   ```bash
   # 不健全タスクを強制停止
   aws ecs stop-task \
     --cluster property-screening-prod \
     --task arn:aws:ecs:us-east-1:xxx:task/... \
     --reason "Manual restart due to health check failure"
   
   # ECS が自動的に新規タスク起動（desired_count = 2）
   # 1～2分待機
   aws ecs wait services-stable \
     --cluster property-screening-prod \
     --services property-screening-backend
   ```

3. **ログ確認**
   ```bash
   aws logs tail /aws/ecs/property-screening-backend --follow
   ```

---

### Case 4: ログ・メトリクス集約の停止

**症状**: CloudWatch Logs・Dashboard に新しいデータが表示されない

**復旧手順**:

1. **ECS タスク ログの確認**
   ```bash
   # CloudWatch Logs グループが存在するか確認
   aws logs describe-log-groups \
     --query 'logGroups[].logGroupName' \
     --output table
   
   # ログストリーム確認
   aws logs describe-log-streams \
     --log-group-name /aws/ecs/property-screening-backend \
     --query 'logStreams[-1].[logStreamName,lastEventTimestamp]'
   ```

2. **ECS タスク定義でログ設定を確認**
   ```bash
   aws ecs describe-task-definition \
     --task-definition property-screening-backend:1 \
     --query 'taskDefinition.containerDefinitions[0].logConfiguration'
   ```

3. **必要に応じて Terraform apply**
   ```bash
   cd infrastructure
   terraform apply -var-file=prod.tfvars -target='module.ecs.aws_ecs_task_definition.app'
   ```

---

## 監視・自動化

### CloudWatch Alarm が発火した場合

| アラーム | アクション |
|---------|---------|
| `ECS-5xx-Errors` | ① CloudWatch Logs で 500 エラー確認 ② ECS Logs → サービス層ログ確認 ③ 必要に応じて Case 3 実行 |
| `RDS-CPU-High` | ① 遅いクエリログ確認 ② インデックス追加・クエリ最適化 ③ インスタンスクラス拡張（Terraform） |
| `RDS-StorageHigh` | ① ストレージ残容量確認 ② ライフサイクルルール確認（S3 削除） ③ RDS ストレージ拡張（Terraform） |
| `ALB-TargetUnhealthy` | Case 3（ECS タスク再起動）を実行 |

### Sentry が異常を検知した場合

**大量の 5xx エラー**:
1. Sentry ダッシュボードでエラースタックトレース確認
2. リリースノート確認（新しいデプロイで何が変わったか）
3. 必要に応じて revert → 新デプロイ

---

## 復旧テストスケジュール

- **毎月初（第 1 営業日 18:00-19:00）**: 
  - Staging DB で PITR テスト
  - チェックリスト確認

- **4 半期ごと（Q 末）**:
  - 本番 DB の dry-run（深夜実施、短時間）
  - 実際に復旧インスタンス起動 → SQL 復元テスト
  - RTO/RPO 測定記録

---

## チェックリスト（復旧完了時）

- [ ] サービス稼働確認（`GET /health` = 200）
- [ ] データベース接続確認（RDS ログに接続成功）
- [ ] CloudWatch ダッシュボード更新確認
- [ ] Sentry エラーなし
- [ ] S3 ファイルアクセス確認（ダミーレポート取得）
- [ ] ユーザーへの通知（ダウンタイム・復旧完了）
- [ ] 事後分析レポート作成（原因・再発防止策）

---

## 参考

- `backup-runbook.md` - バックアップ戦略・手順
- AWS RDS User Guide: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/
- CloudWatch Logs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/
