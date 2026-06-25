# バックアップ・復旧ランブック

対象: 不動産売却スクリーニング（property-sale-screening） / Phase 1（Sprint 3）

## 概要

本ドキュメントは、RDS PostgreSQL と S3 のバックアップ戦略・手順を定義します。

**目標**:
- **RTO（目標復旧時間）**: 30 分以内
- **RPO（目標復旧時点）**: 24 時間以内

---

## RDS バックアップ戦略

### 自動バックアップ設定

**Terraform 設定値**:
```hcl
# infrastructure/modules/rds.tf
resource "aws_db_instance" "postgres" {
  backup_retention_period = 7           # 保持期間：7日
  backup_window          = "02:00-03:00" # UTC 02:00-03:00（日本時間11:00-12:00）
  copy_to_region         = null          # オプション：別リージョンへの複製
  enable_automated_minor_version_upgrade = true
  multi_az               = false         # Phase 1：シングルAZ
  # ...
}
```

**特性**:
- 保持期間内のいずれの時点へも復旧可能（PITR: Point In Time Recovery）
- 毎日自動的に実行、スケジュール逃がしなし
- 復旧時は新規 RDS インスタンスに復元（既存 DB は影響なし）

### 手動スナップショット（本番化前・重要変更前）

**実施タイミング**:
1. Terraform apply で DB スキーマ・テーブル追加時
2. 重要な業務ロジック変更時
3. 本番環境初回デプロイ前

**手順**（AWS Console or CLI）:
```bash
# AWS CLI で手動スナップショット取得
aws rds create-db-snapshot \
  --db-instance-identifier property-screening-prod-db \
  --db-snapshot-identifier property-screening-prod-manual-$(date +%Y%m%d-%H%M%S)

# スナップショット一覧確認
aws rds describe-db-snapshots \
  --db-instance-identifier property-screening-prod-db \
  --query 'DBSnapshots[].{ID:DBSnapshotIdentifier,Created:SnapshotCreateTime,Type:SnapshotType}' \
  --output table
```

**命名規則**:
- 自動: `rds:property-screening-prod-db-2026-06-25-02-00`（自動割り当て）
- 手動: `property-screening-prod-manual-YYYYMMDD-HHMMSS`

---

## S3 バージョニング戦略

### 有効化設定

**Terraform 設定値**:
```hcl
# infrastructure/modules/s3.tf
resource "aws_s3_bucket_versioning" "generated_files" {
  bucket = aws_s3_bucket.generated_files.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ライフサイクル規則：古いバージョンを定期削除
resource "aws_s3_bucket_lifecycle_configuration" "generated_files" {
  bucket = aws_s3_bucket.generated_files.id
  rule {
    id     = "delete-old-versions"
    status = "Enabled"
    noncurrent_version_expiration {
      noncurrent_days = 30  # 30日後に旧バージョン削除
    }
  }
}
```

**特性**:
- すべてのオブジェクトが世代管理される
- 誤削除・上書き時に旧バージョンから復元可能
- 旧バージョンも S3 ストレージ課金対象（ライフサイクル設定で抑制）

### 復旧手順（S3）

**誤削除・上書きの場合**:
```bash
# バージョン一覧確認
aws s3api list-object-versions \
  --bucket property-screening-generated-files \
  --prefix "reports/" \
  --query 'Versions[].[Key,VersionId,LastModified]' \
  --output table

# 目的のバージョンを復元（コピー）
aws s3api get-object \
  --bucket property-screening-generated-files \
  --key "reports/company-123.pdf" \
  --version-id "abc123def456..." \
  "company-123-restored.pdf"
```

---

## 復旧手順（RDS）

### シナリオ 1: データベース全体の復旧（ディザスタリカバリ）

**前提**: Terraform で自動バックアップ保持期間 7 日、PITR 有効

**手順**:

1. **復旧ポイントの決定**
   ```bash
   # 利用可能な復旧期間を確認
   aws rds describe-db-instances \
     --db-instance-identifier property-screening-prod-db \
     --query 'DBInstances[0].{LatestRestorableTime:LatestRestorableTime,EarliestRestorableTime:EarliestRestorableTime}' \
     --output table
   ```

2. **復旧インスタンスの起動**
   ```bash
   # 任意の時点から復旧
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier property-screening-prod-db \
     --target-db-instance-identifier property-screening-prod-db-restored-$(date +%s) \
     --restore-time 2026-06-24T15:00:00Z \
     --db-instance-class db.t3.micro \
     --engine postgres
   
   # 復旧進捗確認（5～10分待機）
   aws rds describe-db-instances \
     --db-instance-identifier property-screening-prod-db-restored-... \
     --query 'DBInstances[0].DBInstanceStatus' \
     --output text
   ```

3. **エンドポイント切替（ダウンタイム < 1 分）**
   ```bash
   # 新しいインスタンスのエンドポイント取得
   aws rds describe-db-instances \
     --db-instance-identifier property-screening-prod-db-restored-... \
     --query 'DBInstances[0].Endpoint.Address' \
     --output text
   
   # .env、Terraform variables 更新、デプロイ
   # 例: TF_VAR_db_host=property-screening-prod-db-restored-xxx.c9akciq32.us-east-1.rds.amazonaws.com
   
   terraform apply -var-file=prod.tfvars
   
   # デプロイ後、古いインスタンス削除（確認後）
   aws rds delete-db-instance \
     --db-instance-identifier property-screening-prod-db \
     --skip-final-snapshot
   ```

### シナリオ 2: 単一テーブル・スキーマの復旧

PITR で復旧インスタンスを作成 → SQL dump → 本番 DB で restore

```bash
# 復旧インスタンスから特定スキーマをダンプ
pg_dump -h property-screening-prod-db-restored-xxx.c9akciq32.us-east-1.rds.amazonaws.com \
  -U postgres -d property_screening \
  --schema public --table scoring_results \
  > scoring_results_backup.sql

# 本番 DB で復元（現在のデータをトランケート後）
psql -h property-screening-prod-db.c9akciq32.us-east-1.rds.amazonaws.com \
  -U postgres -d property_screening \
  -c "TRUNCATE scoring_results CASCADE;"

psql -h property-screening-prod-db.c9akciq32.us-east-1.rds.amazonaws.com \
  -U postgres -d property_screening \
  < scoring_results_backup.sql
```

---

## RTO/RPO 測定

### 実施頻度

- **月 1 回**：復旧テスト実施（テスト用 staging DB で）
- **4 半期ごと**：本番環境での dry-run（夜間、短時間）

### チェックリスト

- [ ] バックアップスナップショットが最新か確認（AWS Console）
- [ ] PITR が有効か確認
- [ ] S3 versioning が有効か確認
- [ ] 復旧インスタンス起動から SQL 復元まで、実際に測定
- [ ] RTO: 30 分以内に復旧完了
- [ ] RPO: 24 時間以内のデータ喪失に留まるか確認

---

## トラブルシューティング

### バックアップが取得されていない

```bash
# 自動バックアップステータス確認
aws rds describe-db-instances \
  --db-instance-identifier property-screening-prod-db \
  --query 'DBInstances[0].{BackupRetentionPeriod:BackupRetentionPeriod,PreferredBackupWindow:PreferredBackupWindow,LatestRestorableTime:LatestRestorableTime}' \
  --output table

# CloudWatch ログで詳細確認
aws logs tail /aws/rds/instance/property-screening-prod-db/error --follow
```

### PITR が利用できない

- 確認点：backup_retention_period が 1 以上か
- 解決：Terraform で backup_retention_period を増やし再適用

---

## 参考

- AWS RDS Backup ドキュメント: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_BackupRestore.html
- PostgreSQL pg_dump: https://www.postgresql.org/docs/14/app-pgdump.html
