# API設計書

> DB設計（`../database/database-design.md`）・要件定義書v2（`../requirements-v2/`）・IPO一覧（`../ipo/ipo.md`）から作成。
> バックエンド＝FastAPI。認証＝JWT（自前認証）。スコア呼称＝構造/イベント/総合。Phase列＝Phase1/Phase2。
> ベースパス：`/api`。リソース中心のREST。一覧系はクエリでフィルタ/ソート/ページネーション。

## 認証・認可

| 項目 | 内容 |
|------|------|
| 認証方式 | JWT（`Authorization: Bearer <token>`）。ログインで発行、`sessions` で失効管理 |
| トークン有効期限 | 8時間（タイムアウト時は復帰先URLを保持し再ログイン） |
| デフォルト権限 | 認証必須（ログイン系を除く全エンドポイント） |
| ロール認可 | `analyst`(担当者)/`manager`(責任者)。**承認/却下は manager のみ**。スクリーニング実行・レポート出力・エクスポート・工数入力は両ロル可 |
| セキュリティ | パスワードポリシー・ログイン試行回数制限＋アカウントロック・認証レート制限（P000） |
| ユーザー管理 | ユーザーは**シード投入／管理者による登録のみ**。セルフサインアップ・公開登録エンドポイントは持たない。パスワード初期化は管理者運用 |

### 共通エラー形式

```json
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "..." } }
```

| ステータス | 意味 | 代表コード |
|-----------|------|-----------|
| 400 | 入力不正・バリデーション違反 | VALIDATION_ERROR |
| 401 | 未認証・トークン無効/期限切れ | UNAUTHORIZED |
| 403 | 認可不足（ロール不一致） | FORBIDDEN |
| 404 | リソース無し | NOT_FOUND |
| 409 | 競合（重複登録・状態不整合） | CONFLICT |
| 422 | 自然言語検索の解釈失敗（条件抽出不能。0件と区別） | NL_PARSE_FAILED |
| 423 | アカウントロック中 | ACCOUNT_LOCKED |
| 429 | レート制限超過 | RATE_LIMITED |
| 500 | サーバ内部エラー | INTERNAL_ERROR |

> 異常系の共通方針（エラー表示＋再試行）に対応。エラーは CloudWatch/Sentry に記録。

## API一覧

| # | エンドポイント | メソッド | 機能(IPO) | 対応テーブル | ロール | Phase |
|---|--------------|---------|------|------------|-------|-------|
| 1 | /api/auth/login | POST | ログイン認証(B1) | users, sessions | 公開 | Phase1 |
| 2 | /api/auth/logout | POST | ログアウト(B5) | sessions | 認証 | Phase1 |
| 3 | /api/auth/me | GET | ロール/自己情報(B2) | users | 認証 | Phase1 |
| 4 | /api/dashboard/kpi | GET | KPIカード(C1) | scoring_results, companies, events | 認証 | Phase1 |
| 5 | /api/events/recent | GET | 直近イベントバナー(C2) | events, qualitative_signals, documents | 認証 | Phase1 |
| 6 | /api/companies | GET | ランキング/フィルタ/検索(C4,C5,C6) | scoring_results⋈companies⋈financial_data⋈events | 認証 | Phase1 |
| 7 | /api/companies/search | POST | 自然言語検索(C6) | companies, scoring_results, financial_data | 認証 | Phase1 |
| 8 | /api/companies/{id} | GET | 企業詳細・根拠(D1–D8) | companies, scoring_results, financial_data, qualitative_signals, documents | 認証 | Phase1 |
| 9 | /api/companies/{id}/report | POST | 根拠レポート出力(D9) | generated_files(+関連READ) | 認証 | Phase1 |
| 10 | /api/screenings | POST | スクリーニング実行(C3) | screening_runs, scoring_results(+パイプライン) | 認証 | Phase1 |
| 11 | /api/screenings/{id} | GET | 実行ステータス取得(C3) | screening_runs | 認証 | Phase1 |
| 12 | /api/longlist | GET | ロングリスト一覧(E1) | longlist_items⋈companies⋈scoring_results | 認証 | Phase1 |
| 13 | /api/longlist | POST | ロングリスト追加(C8,D10) | longlist_items | 認証 | Phase1 |
| 14 | /api/longlist/{id} | PATCH | メモ/ステータス更新(E2,E3) | longlist_items | 認証 | Phase1 |
| 15 | /api/longlist/{id}/approval | POST | 承認/却下(E4) | longlist_items, users | **manager** | Phase1 |
| 16 | /api/longlist/{id} | DELETE | 企業削除(E5) | longlist_items | 認証 | Phase1 |
| 17 | /api/longlist/export | POST | エクスポート(E6) | generated_files(+関連READ) | 認証 | Phase1 |
| 17b | /api/files/{id} | GET | 生成ファイルの状態/署名付きURL取得（report/export共通） | generated_files | 認証 | Phase1 |
| 18 | /api/kpi/effectiveness | GET | 効果検証KPI表示(G1b・読み取り専用) | kpi_snapshots(READ) | 認証 | Phase1 |
| 19 | /api/kpi/effectiveness/trend | GET | KPIトレンド(G3) | kpi_snapshots | 認証 | Phase1 |
| 20 | /api/worklogs | POST | 工数ログ入力(G2) | work_logs | 認証 | Phase1 |
| 21 | /api/watchlist | GET/POST | ウォッチ一覧/登録(F1) | watchlist_items | 認証 | Phase2 |
| 22 | /api/watchlist/{id} | PATCH/DELETE | 条件更新/解除(F1,F2) | watchlist_items | 認証 | Phase2 |
| 23 | /api/notifications | GET | 通知履歴(F3) | notifications | 認証 | Phase2 |
| 24 | /api/notifications/{id} | PATCH | 既読更新(F3) | notifications | 認証 | Phase2 |

---

## エンドポイント詳細

### 1. ログイン

- **Method**: POST ／ **Path**: `/api/auth/login` ／ **対応テーブル**: users, sessions
- **目的**: 認証しJWTを発行（B1）。試行回数制限・ロック・レート制限を適用。

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| email | string | Yes | ログインID（メール） |
| password | string | Yes | パスワード |

```json
{ "email": "sato@example.co.jp", "password": "********" }
```

#### レスポンス（成功 200）

```json
{ "success": true, "data": { "token": "<jwt>", "expires_at": "2026-06-25T20:00:00Z", "role": "analyst" } }
```

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | 入力不備/パスワードポリシー違反 | VALIDATION_ERROR |
| 401 | 認証失敗（汎用メッセージ） | UNAUTHORIZED |
| 423 | アカウントロック中（解除時刻を含む） | ACCOUNT_LOCKED |
| 429 | レート制限超過 | RATE_LIMITED |

---

### 6. 企業ランキング一覧（フィルタ・ソート・検索）

- **Method**: GET ／ **Path**: `/api/companies` ／ **対応テーブル**: scoring_results⋈companies⋈financial_data⋈events
- **目的**: 確定列のランキングを返す（C4/C5/C6 完全一致）。
- **現在値**: 参照する `scoring_results` は **`is_current=true` の実行**に紐づくものに限定（最新の成功実行）。

#### リクエスト（クエリパラメータ）

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| q | string | No | 企業名/証券コードの完全一致検索 |
| industry | string | No | 業種フィルタ |
| market_cap_band | string | No | 時価総額帯 |
| score_band | string | No | スコア帯 |
| has_event | boolean | No | イベント有無 |
| sort | enum(total,structure,event) | No | 並び替えキー（既定=total 降順） |
| page / per_page | integer | No | ページネーション |

#### レスポンス（成功 200）

```json
{
  "success": true,
  "data": {
    "items": [
      { "company_id": "uuid", "name": "○○HD", "securities_code": "1234", "industry": "小売",
        "structure_score": 82.5, "event_score": 64.0, "total_score": 91.2,
        "pbr": 0.78, "unrealized_gain": 540.0, "event_boost": 1.30,
        "confidence": "high", "has_event": true }
    ],
    "page": 1, "per_page": 50, "total": 100
  }
}
```

---

### 7. 自然言語検索

- **Method**: POST ／ **Path**: `/api/companies/search` ／ **対応テーブル**: companies, scoring_results, financial_data
- **目的**: 自然言語クエリをAgentが条件抽出し、収集済みデータセット（企業マスタ＋総合スコア）へ絞り込み（C6）。バッチ収集の再実行ではない。

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| query | string(≤200) | Yes | 自然言語クエリ（例「含み益500億円以上・関西・小売」） |

#### レスポンス（成功 200）

```json
{ "success": true, "data": { "extracted_filters": { "unrealized_gain_min": 500, "region": "関西", "industry": "小売" },
  "summary": "条件に合致する企業は12社…", "items": [ /* 企業ランキング項目と同形 */ ] } }
```

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | 文字数超過/空 | VALIDATION_ERROR |
| 422 | 解釈失敗（条件抽出不能。0件と区別） | NL_PARSE_FAILED |

---

### 8. 企業詳細（根拠レポート）

- **Method**: GET ／ **Path**: `/api/companies/{id}` ／ **対応テーブル**: companies, scoring_results, financial_data, qualitative_signals, documents
- **目的**: 1社のスコア内訳・定量指標・定性シグナル（支持/反証）・出典・AI総合判定を返す（D1–D8）。トレース可能率100%。
- **現在値**: スコアは **`is_current=true` の実行**の `scoring_results` を参照。

#### レスポンス（成功 200・抜粋）

```json
{
  "success": true,
  "data": {
    "company": { "id": "uuid", "name": "○○HD", "securities_code": "1234", "industry": "小売", "market_cap": 3200.0 },
    "scores": { "structure": 82.5, "event": 64.0, "total": 91.2, "event_boost": 1.30, "confidence": "high" },
    "financials": { "pbr": 0.78, "adjusted_pbr": 0.55, "equity_ratio": 0.62,
      "re_market_value": 1200.0, "re_book_value": 660.0, "unrealized_gain": 540.0,
      "unrealized_gain_ratio": 0.17, "roic": 0.03, "wacc": 0.06, "roic_below_wacc": true },
    "signals": [
      { "type": "activist_proposal", "stance": "support", "strength": 0.9,
        "source": { "document_type": "large_shareholding", "source_page": 12,
          "quote": "…不動産の売却を求める…", "url": "https://disclosure..." } },
      { "type": "core_business", "stance": "counter", "quote": "…当該不動産は中核事業…" }
    ],
    "ai_judgment": { "comment": "売却可能性は高い…", "evidence_refs": ["signal:uuid", "metric:pbr"] }
  }
}
```

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 404 | 企業が存在しない | NOT_FOUND |

> 出典の外部リンク切れ時はクライアント側で「リンク無効」表示（document_type/source_page/引用文は保持）。

---

### 9. 根拠レポート出力

- **Method**: POST ／ **Path**: `/api/companies/{id}/report` ／ **対応テーブル**: generated_files（+関連READ）
- **目的**: 当該企業の根拠レポートを生成しS3保管（D9、両ロール可）。

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| format | enum(pdf,pptx) | Yes | 出力形式（最小PDF） |

#### レスポンス（成功 202・非同期）

重い生成を想定し非同期に統一。生成は202＋`file_id`/statusを返し、完了後に `GET /api/files/{id}` で署名付きURLを取得する。

```json
{ "success": true, "data": { "file_id": "uuid", "format": "pdf", "status": "generating" } }
```

| 500 | 生成失敗（再試行導線） | REPORT_GENERATION_FAILED |

---

### 9b. 生成ファイルの状態/取得（report・export 共通）

- **Method**: GET ／ **Path**: `/api/files/{id}` ／ **対応テーブル**: generated_files
- **目的**: 非同期生成したレポート/エクスポートの状態を取得し、完了時にS3署名付きURLを返す。

#### レスポンス（成功 200）

```json
{ "success": true, "data": { "file_id": "uuid", "file_kind": "report", "format": "pdf",
  "status": "ready|generating|failed", "download_url": "https://s3-signed-url..." } }
```

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 404 | ファイルが存在しない | NOT_FOUND |
| 500 | 生成失敗 | FILE_GENERATION_FAILED |

---

### 10–11. スクリーニング実行（非同期）＋ステータス取得

- **POST `/api/screenings`**（C3）：母集団に対し一括スコアリングを起動。両ロール可。
  - **スコープ**：母集団データは事前バッチで投入済みのため、本実行は原則 **A2–A5（構造スコア算出→定性シグナル抽出→イベントスコア→統合スコア・確信度・AI判定）** を対象とする。EDINET/YFinanceからのデータ収集（**A1**）は別のバックグラウンド/バッチ処理であり、本APIのスコープ外（下記「データ取込バッチ」参照）。
  - レスポンス（202）：`{ "success": true, "data": { "run_id": "uuid", "status": "running" } }`
- **GET `/api/screenings/{id}`**：ポーリングで進捗取得。
  - レスポンス（200）：`{ "success": true, "data": { "run_id": "uuid", "status": "success|running|failed", "finished_at": "...", "duration_ms": 41000 } }`
  - 失敗時：status=failed＋クライアントはエラー表示＋再試行。500=INTERNAL_ERROR。

---

### 13. ロングリスト追加（一括）

- **Method**: POST ／ **Path**: `/api/longlist` ／ **対応テーブル**: longlist_items
- **目的**: 選択企業を一括登録（C8/D10、重複排除）。

#### リクエスト

```json
{ "company_ids": ["uuid1", "uuid2"] }
```

#### レスポンス（成功 201）

```json
{ "success": true, "data": { "added": 2, "skipped_duplicates": 0 } }
```

| 409 | 既に登録済み（UNIQUE(company_id)） | CONFLICT |

---

### 14–16. ロングリスト更新／承認／削除

- **PATCH `/api/longlist/{id}`**（E2/E3）：`{ "reason_memo": "…(≤500)", "status": "candidate" }`。500字超過は400=VALIDATION_ERROR。
- **POST `/api/longlist/{id}/approval`**（E4・**manager のみ**）：`{ "decision": "approved" | "rejected" }`。analystは403=FORBIDDEN。
- **DELETE `/api/longlist/{id}`**（E5）：削除。204。

---

### 17. ロングリストのエクスポート

- **Method**: POST ／ **Path**: `/api/longlist/export` ／ **対応テーブル**: generated_files（+関連READ）
- **目的**: 確定出力項目（各スコア・含み益・出典サマリ等）を CSV/Excel 生成（E6）。

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| format | enum(csv,excel) | Yes | 出力形式 |

#### レスポンス（成功 202・非同期）

レポート出力と同方針で非同期に統一。202＋`file_id`/statusを返し、完了後に `GET /api/files/{id}` で署名付きURLを取得する。

```json
{ "success": true, "data": { "file_id": "uuid", "format": "csv", "status": "generating" } }
```

| 409 | 対象0件（ボタン無効化と整合） | EMPTY_TARGET |
| 500 | 生成失敗（再試行導線） | EXPORT_GENERATION_FAILED |

---

### 18. 効果検証KPI

- **Method**: GET ／ **Path**: `/api/kpi/effectiveness` ／ **対応テーブル**: kpi_snapshots（+導出元READ）
- **目的**: 工数削減・品質標準化（再現性）・カバレッジ・トレース可能率・平均構造スコアを返す（G1b）。
- **読み取り専用**: 最新の `kpi_snapshots` を**読み取り表示**する（GETで書き込みは行わない）。スナップショット生成（G1a）は実行完了フック/バッチが担う（API非公開）。導出元のカバレッジ等は `is_current=true` の実行を母数とする。

#### リクエスト（クエリ）

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| period_from / period_to | date | No | 集計対象期間 |

#### レスポンス（成功 200）

```json
{ "success": true, "data": {
  "period": "2026-04-01/2026-06-30",
  "universe_coverage": 100.0, "traceability_rate": 100.0,
  "avg_structure_score": 58.4, "reproducibility_score": 98.0,
  "total_workload_min": 60, "workload_reduction_rate": 99.8 } }
```

---

### 20. 工数ログ入力

- **Method**: POST ／ **Path**: `/api/worklogs` ／ **対応テーブル**: work_logs
- **目的**: 工数削減の計測元を手入力で蓄積（G2、両ロール可）。

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| task_type | enum(primary_screening,deep_dive,report,other) | Yes | タスク種別 |
| duration_min | integer | Yes | 所要時間（分） |
| screening_run_id | uuid | No | 紐づく実行 |
| period_label | string | No | 対象期間ラベル |
| logged_on | date | Yes | 記録日 |

#### レスポンス（成功 201）

```json
{ "success": true, "data": { "id": "uuid" } }
```

---

### Phase2（21–24）通知・ウォッチリスト

| エンドポイント | メソッド | 概要 |
|--------------|---------|------|
| /api/watchlist | GET/POST | ウォッチ一覧取得／登録（重複は409） |
| /api/watchlist/{id} | PATCH/DELETE | 通知条件更新（notify_conditions）／解除 |
| /api/notifications | GET | 通知履歴（既読/未読、ページネーション） |
| /api/notifications/{id} | PATCH | 既読化（`{ "is_read": true }`） |

> 通知の送出はバックグラウンド処理（A8）が `scoring_results`/`events` を監視し `notifications` を生成。APIは参照/既読更新を担う。

---

## 設計メモ

- **REST原則**：リソース中心（companies/longlist/screenings/worklogs…）。複雑な絞り込みはクエリパラメータ、一覧はページネーション＋ソート。
- **非同期**：スクリーニング実行は 202＋run_idを返し、`GET /screenings/{id}` でポーリング（将来WebSocket/SSE化も可）。レポート(9)・エクスポート(17)も同方針で **202＋file_id/status** を返し、`GET /api/files/{id}`(9b) で状態確認・署名付きURL取得に統一。
- **ファイル**：レポート/エクスポートは生成後 S3 署名付きURLを返す（DBにファイルを持たない原則）。
- **現在の有効スコアセット**：ランキング(6)・詳細(8)・KPI(4)・効果検証(18) が参照する `scoring_results` は **`is_current=true` の最新成功実行**に限定する（`screening_runs.is_current`）。実行成功時に当該runをtrue・他をfalseへ原子的更新。
- **KPIスナップショット生成（API非公開）**：`kpi_snapshots`(G1a) はスクリーニング実行完了フックまたはスケジュールバッチで生成。`GET /api/kpi/effectiveness`(G1b) は最新スナップショットの**読み取り専用**で書き込まない。
- **バッチ系・内部処理は API非公開**：A1（EDINET/YFinanceデータ取込）・A6（バックテスト）・A7（HITL学習）・A8（通知トリガー）、および `scoring_parameters`（較正パラメータ/学習重み）は**内部利用・API非公開**。スクリーニング実行API（10）は収集済みデータに対する A2–A5 のスコアリングを担う。
- **N+1回避**：`GET /companies/{id}` は `signals⋈documents` を、ランキング(6)は `scoring_results⋈companies⋈financial_data` を **JOIN/eager loading で一括取得**し N+1 を避ける。
- **ロングリストの制約前提**：`longlist_items` の `UNIQUE(company_id)` は**部内共有の単一ロングリスト**前提（担当者別リストは持たない）。業務要件が変われば制約を見直す。
- **認可の集約**：manager限定は `/longlist/{id}/approval` のみ。他の実行系は両ロール可（要件と一致）。
- **トレーサビリティ**：`/companies/{id}` のsignals.sourceに document_type・source_page・quote・url を必ず含め、トレース可能率100%をAPIレベルで担保。
