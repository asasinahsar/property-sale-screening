# Feature 開発実装計画（Phase 1 以降）

## 概要

このドキュメントは、Foundation Phase（Slice 0-1～0-7）の完了後、Phase 1 以降の Feature 開発を計画したものです。

Vertical Slice Architecture（VSA）に基づいて機能を分割し、
フロントエンド（Next.js 15 App Router + MUI + orval）とバックエンド（FastAPI + SQLAlchemy 2.0 async + PostgreSQL）を並行して開発します。

**【重要】非機能要件（負荷テスト・冗長化・バックアップ・監視）も Phase 1 に含め、デプロイ前に実施。**

## 前提条件

✅ **Foundation Phase（Slice 0-1～0-7）完了済み**
- FastAPI バックエンド初期化、users/sessions/company/screening 等の ORM モデル実装済み
- PostgreSQL Docker セットアップ＆マイグレーション初期スキーマ実施
- Next.js 15（App Router）フロントエンド初期化
- 自前認証基盤（JWT + httpOnly Cookie）実装済み
- API 統合テスト基盤構築完了

詳細は最新の git ログ「foundation phase 完了」を参照。

---

## スライス分割戦略

このプロジェクトは**不動産売却スクリーニング**を自動化する AI × Web アプリケーション。
以下の方針に基づいてスライス分割します：

1. **フロント・バック両面の実装完結**：各スライスで Backend（API層）と Frontend（画面）が一貫して動作
2. **依存関係の明確化**：スライス間の依存を正確に把握し、直列化・並列化を明示
3. **実装期間の目安**：大多数は 1～2 日。Slice 2（コアロジック）は約 1 週間。Slice N（非機能・インフラ）は 1～2 週間（並行実施）
4. **LLM Agent 活用**：スコアリング・推論が必要な機能（Slice 2, 7）では ReAct パターンの自律 Agent を採用
5. **AWS クラウド前提**：ECS Fargate・RDS PostgreSQL・S3・CloudWatch を前提

---

## Phase 1：MVPスクリーニング機能（Slice 1～5）+ 非機能・インフラ・運用（Slice N）

### Slice 1: 認証・セッション管理の完成＆Dashboard骨組み

**概要**：
Foundation で実装した JWT 認証を完成させ、ログイン画面（P000）を完成。
ダッシュボード（P001）のスケルトンを構築し、Backend API との疎通確認まで実施。

**実装期間**: 1～2 日

**対応画面（フロント）**：
- P000 ログイン（認証・認可）
- P001 ダッシュボード（スケルトン：KPIカード枠・フィルタ枠）

**API エンドポイント（バック）**：
- `POST /api/auth/login` ← JWT トークン発行、sessions 作成、セッション失効管理
- `POST /api/auth/logout` ← セッション破棄
- `GET /api/auth/me` ← ロール/自己情報確認
- `GET /api/dashboard/kpi` ← KPI集計（スケルトン：仮値）
- `GET /health` ← ヘルスチェック（ALB用）

**関連テーブル・モデル**：
- users（login_email, password_hash, role, failed_login_count, locked_until）
- sessions（user_id, token, expires_at, return_url）← **タイムアウト復帰対応**
- companies（is_universe, 母集団フラグ）

**実装順序**：
1. **バックエンド**：
   - `POST /api/auth/login` 実装：メール/パスワード照合 → JWT生成 → sessions.create
   - パスワードポリシー・試行回数制限・アカウントロック機構
   - `POST /api/auth/logout`、`GET /api/auth/me`
   - `GET /api/dashboard/kpi` スケルトン（仮値返却）
   - **`GET /health` ← ヘルスチェックエンドポイント（Slice N の冗長化で必須）**
   - pytest で全エンドポイントのテスト（疎通確認のみ）

2. **フロントエンド**：
   - P000 ログイン画面（email/password フォーム、エラーハンドリング、loading状態）
   - Login フィーチャー実装：`useLogin` hook（TanStack Query）、Login form component
   - P001 スケルトン：KPI カード枠、フィルタ枠、テーブル枠（データなし）
   - Navigation/Layout 完成：ログイン後の基本レイアウト

3. **統合テスト**：
   - E2E：ログイン → P001 遷移 → ログアウト の一連が機能するか確認

**チェックリスト**：
- [ ] `POST /api/auth/login` 実装・テスト完了
- [ ] パスワードポリシー・ロック機構 実装・テスト完了
- [ ] **`GET /health` ヘルスチェック実装**
- [ ] P000 ログイン画面 UI 完成・デザイン適用
- [ ] P001 スケルトン画面レイアウト確認
- [ ] E2E ログイン～表示までの疎通確認
- [ ] orval 再生成・型チェック完了

**参考**：
- `.claude/rules/three-layer-architecture.md` - Backend 3層設計
- `.claude/rules/tdd-guide.md` - Red-Green-Refactor サイクル
- `docs/requirements/api/api-design.md` - エンドポイント詳細
- `docs/requirements/requirements-v2/P000_ログイン.md` - 認証セキュリティ要件

---

### Slice 2: スコアリングパイプライン＆ダッシュボード KPI 表示

**概要**：
Core ロジック。母集団企業に対して「構造スコア（定量）」「イベントスコア（定性）」を算出し、
「総合スコア」を生成。LLM Agent（ReAct パターン）を活用して定性シグナル抽出。
ダッシュボードのKPI カード・企業ランキングテーブルを実装。

**実装期間**: **約 1 週間**（複数機能を順序立てて TDD で実装）

**対応画面（フロント）**：
- P001 ダッシュボード：KPI カード（対象企業数・高構造スコア社数・平均スコア・イベント件数）、企業ランキングテーブル

**API エンドポイント（バック）**：
- `POST /api/screenings` ← 一括スコアリング実行（非同期 202+run_id）
- `GET /api/screenings/{id}` ← 実行ステータス取得（進捗ポーリング）
- `GET /api/dashboard/kpi` ← KPI カード（確定値）
- `GET /api/companies` ← ランキング一覧（filtering/sorting/pagination）

**関連テーブル・モデル**：
- companies（企業マスタ）
- financial_data（PBR・含み益・ROIC/WACC 等の定量指標）
- documents（開示文書・S3 キー）
- qualitative_signals（定性シグナル：activist_proposal/capital_efficiency_target/sale_suggestion）
- screening_runs（スクリーニング実行単位・is_current フラグ）
- scoring_results（実行×企業のスコア・確信度・AI判定）

**実装の段階化（TDD サイクル順序）**：

Slice 2 は以下の 4 機能を順序立てて実装します。各ステップで 🔴RED（テスト作成）→ 🟢GREEN（実装）→ 🔵REFACTOR を回します：

#### Step 2-1: 構造スコア算出ロジック（1～2 日）
- **入力**: financial_data テーブルの定量指標（PBR, 含み益, 自己資本比率, ROIC, WACC 等）
- **処理**: 
  - 🔴 Pydantic schema 設計：FinancialDataSchema, StructureScoreInputSchema
  - 🔴 テスト：業種内 z-score 正規化、合成スコア算出の計算ロジックテスト、境界値確認
  - 🟢 Service 層実装：`StructureScoringService.calculate()`
    - 財務指標の業種内 z-score 正規化
    - 複数指標の加重平均で合成（0–100）
    - 出力：structure_score + 寄与内訳 breakdown（各指標の寄与率）
  - 🟢 Repository 層：scoring_results にスコア保存
  - 🔵 テストパス・リファクタリング
- **出力**: structure_score（0–100）、指標別寄与内訳

#### Step 2-2: 定性シグナル抽出（LLM Agent、ReAct パターン）（2～3 日）
- **入力**: documents テーブルの開示文書（S3 キー）、AIが読み込み対象とする metadata
- **処理**:
  - 🔴 Pydantic schema 設計：QualitativeSignalSchema, SignalExtractionRequestSchema, SignalExtractionResponseSchema（後述「LLM Agent ガイダンス」参照）
  - 🔴 テスト：Mock LLM（Fixed Response）を使用、想定 signal_type・引用文・ページが正確に抽出されるか確認
  - 🟢 **LLM Agent 実装** — ReAct パターン（`backend/app/llm/agent.py`）
    - 開示文書（document.s3_key）を S3 から読み込み（またはキャッシュ）
    - signal_type（`activist_proposal`, `capital_efficiency_target`, `sale_suggestion`）を LLM が自動抽出
    - **必須**: document_id, source_page, quote_text を紐づけ（出典担保）
    - 出典がないシグナルは不採用（品質管理）
    - エラー処理：LLM 呼び出し失敗時は `503 INTERNAL_ERROR` を返す（リトライ対応）
  - 🟢 Service 層実装：`QualitativeSignalService.extract_and_persist()`
    - LLM Agent 呼び出し（LLM ロジックはサービス層に閉じ込める）
    - 抽出結果を qualitative_signals テーブルに永続化
  - 🔵 テストパス・LLM 呼び出し部分をモック化してユニットテスト確保
- **出力**: qualitative_signals（signal_type, stance, strength, source_document）

#### Step 2-3: イベントスコア算出ロジック（1～2 日）
- **入力**: qualitative_signals テーブルの抽出済み定性シグナル、大量保有報告書
- **処理**:
  - 🔴 Pydantic schema 設計：EventScoringInputSchema, EventScoreOutputSchema
  - 🔴 テスト：シグナル種別×強度の重み付け、recency 加点、反証減点ロジックのテスト、境界値確認
  - 🟢 Service 層実装：`EventScoringService.calculate()`
    - シグナル種別（activist_proposal, capital_efficiency_target, sale_suggestion）ごとに重み付け
    - 強度（0.0–1.0）を加点・減点に変換
    - recency 考慮：最新シグナルほど加点
    - 反証があれば減点
    - 出力：event_score（0–100）+ イベントブースト倍率（1.0–2.0）
  - 🔵 テストパス・リファクタリング
- **出力**: event_score（0–100）、イベントブースト倍率

#### Step 2-4: 統合スコア・確信度・AI 判定生成（1～2 日）
- **入力**: structure_score, event_score, scoring_results（スコアリング履歴）
- **処理**:
  - 🔴 Pydantic schema 設計：IntegratedScoringSchema, ConfidenceSchema, AIJudgmentSchema
  - 🔴 テスト：total_score = f(structure_score, event_score, event_boost) の計算テスト、confidence 判定ロジック
  - 🟢 Service 層実装：`IntegrationScoringService.integrate()`
    - total_score = f(structure_score, event_score, event_boost) 計算（重み付け）
    - confidence = High/Mid/Low 判定（データ充足度・出典数に基づく）
    - **AI 総合判定コメント生成**（LLM Agent 呼び出し可、オプション）
      - 判定コメントに参照根拠（signal_id, metric_id）を必ず紐づけ（トレース可能率 100%）
  - 🟢 Repository 層：screening_runs.create、scoring_results.bulk_create
    - is_current フラグ原子的更新：新規 run を is_current=true に、旧 run を is_current=false に
  - 🟢 API エンドポイント実装
    - `POST /api/screenings` ← 非同期実行キック（202 + run_id）
    - `GET /api/screenings/{id}` ← ステータス・進捗ポーリング用
    - `GET /api/dashboard/kpi` ← KPI 確定値返却
    - `GET /api/companies` ← ランキング一覧（is_current=true のスコアのみ）
  - 🔵 pytest：structure/event/total の計算・各値の境界値確認
- **出力**: total_score、confidence、AI判定コメント、参照根拠 mapping

#### Slice 2 全体統合テスト
- スコアリング実行の非同期進捗確認（ポーリング動作）
- ランキングが総合スコア降順で表示されるか確認
- N+1 回避（JOIN/eager loading）の確認

**フロントエンド実装（Slice 2 と並列）**：
- Companies フィーチャー実装：
  - `useGetCompanies` hook（orval wrap、filtering/sorting/pagination）
  - `useGetScreeningStatus` hook（ステータスポーリング）
- Dashboard コンポーネント実装：
  - KPI Card コンポーネント（数値表示・カラーコード）
  - CompanyRankingTable コンポーネント（企業名/業種/各スコア/含み益/イベント/詳細ボタン）
  - フィルタ UI（業種・時価総額帯・スコア帯・イベント有無）、ソートトグル
  - スクリーニング実行ボタン（非同期待ち）、再読込ボタン

**チェックリスト**：
- [ ] **Step 2-1**: 構造スコア算出ロジック実装・テスト完了
- [ ] **Step 2-2**: LLM Agent（定性シグナル抽出）実装・テスト完了（Mock LLM で検証）
- [ ] **Step 2-3**: イベントスコア算出ロジック実装・テスト完了
- [ ] **Step 2-4**: 統合スコア・確信度・AI判定実装・テスト完了
- [ ] `POST /api/screenings` 実装・非同期確認
- [ ] `GET /api/screenings/{id}` ポーリング動作確認
- [ ] `GET /api/companies` filtering/sorting 実装
- [ ] Dashboard KPI・ランキング表示確認
- [ ] orval 再生成・型チェック完了

**注**：
- S3 への開示文書アップロード（A1 データ取込）は Slice 外。テスト用ダミー文書を事前投入。
- LLM Agent は Anthropic Claude（Open Responses API）を使用。環境変数に API キー保持。

**参考**：
- `docs/requirements/specifications/scoring-and-pipeline.md` - スコア計算式
- `docs/requirements/ipo/ipo.md` A2～A5 セクション
- `.claude/rules/vsa-guide.md` - VSA 設計の再確認

---

### LLM Agent 実装ガイダンス（Slice 2, 7 共通）

Slice 2（定性シグナル抽出）と Slice 7（自然言語検索条件抽出）で LLM Agent（ReAct パターン）を使用します。
以下のガイダンスに従い、テスト可能・管理可能な実装を行ってください。

#### 基本方針

- **LLM 呼び出しはサービス層に閉じ込める**: Repository 層・API 層では LLM を呼び出さない（CLAUDE.md ルール）
- **入出力を Pydantic で型定義**: schema 層で LLM のリクエスト・レスポンス形式を明示的に管理
- **テストは Mock LLM で実施**: 実 API 呼び出しではなく Fixed Response を用いて高速化・コスト削減
- **エラーハンドリング明確化**: LLM 呼び出し失敗・解釈失敗時の HTTP ステータスコード・エラーコードを明記

#### Slice 2-2: 定性シグナル抽出の Pydantic スキーマ例

```python
# backend/app/api/v1/schemas/qualitative_signal.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class SignalTypeEnum(str, Enum):
    ACTIVIST_PROPOSAL = "activist_proposal"
    CAPITAL_EFFICIENCY_TARGET = "capital_efficiency_target"
    SALE_SUGGESTION = "sale_suggestion"

class StanceEnum(str, Enum):
    SUPPORT = "support"
    COUNTER = "counter"

class SignalExtractionRequestSchema(BaseModel):
    """LLM Agent へのリクエスト"""
    document_id: str = Field(..., description="開示文書 UUID")
    document_text: str = Field(..., description="開示文書の本文（S3 から読み込み）")
    company_name: str = Field(..., description="対象企業名")
    
class ExtractedSignalSchema(BaseModel):
    """LLM Agent が抽出した単一シグナル"""
    signal_type: SignalTypeEnum
    stance: StanceEnum
    strength: float = Field(..., ge=0.0, le=1.0, description="シグナル強度")
    quote_text: str = Field(..., description="引用文（出典必須）")
    source_page: int = Field(..., description="ページ番号")

class SignalExtractionResponseSchema(BaseModel):
    """LLM Agent からのレスポンス"""
    signals: List[ExtractedSignalSchema]
    summary: str = Field(..., description="抽出の説明コメント")
```

#### Slice 2-2: LLM Agent テスト方法（Mock LLM）

```python
# backend/tests/test_qualitative_signal.py
import pytest
from app.services.qualitative_signal import QualitativeSignalService
from app.api.v1.schemas.qualitative_signal import (
    SignalExtractionRequestSchema, 
    ExtractedSignalSchema,
    SignalTypeEnum, 
    StanceEnum
)

class MockLLMAgent:
    """テスト用 Mock LLM Agent"""
    def __call__(self, request: SignalExtractionRequestSchema) -> List[ExtractedSignalSchema]:
        # Fixed Response: 常に決まった結果を返す
        return [
            ExtractedSignalSchema(
                signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
                stance=StanceEnum.SUPPORT,
                strength=0.85,
                quote_text="当社は不動産売却を提案する",
                source_page=12
            )
        ]

@pytest.fixture
def mock_llm_agent():
    return MockLLMAgent()

def test_extract_signals_success(mock_llm_agent):
    """定性シグナル抽出が正常に動作することを確認"""
    service = QualitativeSignalService(llm_agent=mock_llm_agent)
    
    request = SignalExtractionRequestSchema(
        document_id="doc-123",
        document_text="アクティビスト投資家が当社に対し...",
        company_name="ABC Corp"
    )
    
    signals = service.extract_signals(request)
    
    assert len(signals) == 1
    assert signals[0].signal_type == SignalTypeEnum.ACTIVIST_PROPOSAL
    assert signals[0].strength == 0.85
    assert signals[0].source_page == 12

def test_extract_signals_no_match():
    """シグナルが抽出されない場合（空結果）を確認"""
    class EmptyMockLLM:
        def __call__(self, request):
            return []
    
    service = QualitativeSignalService(llm_agent=EmptyMockLLM())
    
    request = SignalExtractionRequestSchema(
        document_id="doc-456",
        document_text="通常の事業報告書...",
        company_name="XYZ Corp"
    )
    
    signals = service.extract_signals(request)
    assert len(signals) == 0
```

#### Slice 2-2: エラーハンドリング（解釈失敗時）

```python
# backend/app/services/qualitative_signal.py
from fastapi import HTTPException, status

class QualitativeSignalService:
    def extract_signals(self, request: SignalExtractionRequestSchema):
        try:
            # LLM Agent 呼び出し（サービス層に閉じ込める）
            response = self.llm_agent(request)
        except Exception as e:
            # LLM 呼び出し失敗時は 503 Internal Server Error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "LLM_CALL_FAILED", "message": str(e)}
            )
        
        # 抽出失敗（シグナルなし）は正常系として扱う（空リスト返却）
        if not response.signals:
            return []
        
        return response.signals
```

#### Slice 7: 自然言語検索条件抽出の Pydantic スキーマ例

```python
# backend/app/api/v1/schemas/company_search.py
from pydantic import BaseModel, Field
from typing import Optional

class SearchConditionSchema(BaseModel):
    """抽出された検索条件"""
    unrealized_gain_min: Optional[float] = Field(None, description="含み益下限（億円）")
    unrealized_gain_max: Optional[float] = Field(None, description="含み益上限（億円）")
    region: Optional[str] = Field(None, description="地域（例：関西）")
    industry: Optional[str] = Field(None, description="業種（例：小売）")
    pbr_max: Optional[float] = Field(None, description="PBR 上限（例：1.0）")

class NLSearchRequestSchema(BaseModel):
    """ユーザーの自然言語クエリ"""
    query: str = Field(..., max_length=200, description="検索クエリ")

class NLSearchResponseSchema(BaseModel):
    """条件抽出結果"""
    extracted_filters: SearchConditionSchema
    summary: str = Field(..., description="抽出結果の説明")
    items_count: int = Field(..., description="マッチ企業数")
```

#### Slice 7: 条件抽出テスト（Mock LLM）

```python
# backend/tests/test_company_search.py
import pytest
from app.services.company_search import CompanySearchService
from app.api.v1.schemas.company_search import SearchConditionSchema

class MockNLSearchAgent:
    """テスト用 Mock 自然言語検索 Agent"""
    def __call__(self, query: str) -> SearchConditionSchema:
        # Fixed Response
        if "含み益500" in query and "小売" in query:
            return SearchConditionSchema(
                unrealized_gain_min=500.0,
                industry="小売"
            )
        else:
            raise ValueError("Parsing failed")

@pytest.fixture
def mock_nl_agent():
    return MockNLSearchAgent()

def test_nl_search_success(mock_nl_agent):
    """自然言語クエリから条件が正確に抽出されることを確認"""
    service = CompanySearchService(nl_agent=mock_nl_agent)
    
    query = "含み益500億円以上・小売業の企業を探してください"
    result = service.search(query)
    
    assert result.extracted_filters.unrealized_gain_min == 500.0
    assert result.extracted_filters.industry == "小売"

def test_nl_search_parse_failed(mock_nl_agent):
    """解釈失敗時に 422 NL_PARSE_FAILED を返すことを確認"""
    service = CompanySearchService(nl_agent=mock_nl_agent)
    
    query = "意図不明なクエリ..."
    
    with pytest.raises(HTTPException) as exc:
        service.search(query)
    
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "NL_PARSE_FAILED"
```

#### 費用・レート制限対策

1. **Mock LLM の活用**：開発・テスト中は実 API 呼び出しを避け、Mock LLM でテスト
2. **バッチ処理による集約**：複数企業のシグナル抽出は 1 回の API 呼び出しにまとめる（可能な範囲で）
3. **キャッシング**：同じ document に対する抽出結果をキャッシュして再利用
4. **レート制限の監視**：API 呼び出し前に残り quota を確認、超過見込み時は 429 を返す
5. **環境変数で API キー・モード切り替え**：
   ```python
   # backend/.env
   LLM_PROVIDER=anthropic  # or mock
   LLM_API_KEY=sk-...
   LLM_MODE=production    # or test
   ```

#### Slice 2-2, 7 実装時の注意

- **ユニットテスト必須**：Mock LLM でテストを高速化・確実化
- **統合テストは慎重に**：実 API 呼び出しを使う場合は事前に cost 計算
- **出典の完全性**：シグナル抽出時に document_id, source_page, quote_text が 100% 付与されるか確認
- **エラーハンドリング明確化**：LLM 失敗 (503)、解釈失敗 (422)、その他 (500) を区別

---

### Slice 3: 企業詳細・根拠レポート（P002）

**概要**：
1社のスコア内訳・定量指標・定性シグナル（支持/反証）・出典を 1ページで表示し、
トレース可能率100%を達成。AI総合判定コメント付き。PDF/PowerPoint 根拠レポート出力機能。

**実装期間**: 2～3 日

**対応画面（フロント）**：
- P002 企業詳細（根拠レポート）

**API エンドポイント（バック）**：
- `GET /api/companies/{id}` ← 企業詳細・スコア内訳・定量指標・定性シグナル・出典一式
- `POST /api/companies/{id}/report` ← PDF/PowerPoint 生成（非同期 202+file_id）
- `GET /api/files/{id}` ← ファイルの状態・署名付き URL 取得（report/export 共通）

**関連テーブル・モデル**：
- companies（企業マスタ）
- financial_data（定量指標）
- scoring_results（スコア・確信度・AI判定）
- qualitative_signals（定性シグナル）⋈ documents（出典文書）
- generated_files（レポート成果物）

**実装順序**：
1. **バックエンド**：
   - Schema 設計：CompanyDetailSchema（scores + financials + signals + ai_judgment）
   - `GET /api/companies/{id}` 実装：
     - N+1 回避：signals⋈documents を eager loading
     - 返却内容：企業基本情報・スコア・定量指標・定性シグナル（支持/反証別）・確信度・AI判定参照根拠
     - JSON 応答でドキュメント type・page・引用文を必須含有
   - レポート生成ロジック（Service 層）：
     - PDF テンプレート（jinja2/weasyprint）に企業データ・スコア・根拠を流し込み
     - 最小 PDF 出力、PowerPoint はオプション（Phase 2）
     - S3 へアップロード・署名付き URL 生成
   - `GET /api/files/{id}`：状態確認・URL返却
   - pytest：詳細エンドポイント・出典整合性テスト

2. **フロントエンド**：
   - CompanyDetail フィーチャー実装：
     - `useGetCompanyDetail` hook
   - CompanyDetail コンポーネント：
     - 企業ヘッダ（名前・コード・業種・時価総額）
     - 総合スコア＋構造/イベント内訳（レーダー）
     - 定量指標テーブル（指標名・数値・寄与・出典）
     - ROIC vs WACC 対比（ROIC<WACC 強調）
     - 定性シグナルカード（支持/反証区別・引用文・出典リンク）
     - AI判定パネル
     - レポート出力ボタン（PDF）& ロングリスト追加ボタン

3. **統合テスト**：
   - 企業詳細ページのロード・データ整合性確認
   - PDF 生成の成功・ダウンロード確認

**チェックリスト**：
- [ ] `GET /api/companies/{id}` 実装・出典整合テスト完了
- [ ] PDF レポート生成実装・テスト完了
- [ ] `GET /api/files/{id}` 実装
- [ ] P002 企業詳細 UI 完成・デザイン適用
- [ ] スコア内訳チャート実装（レーダー）
- [ ] 出典トレース機能確認

**参考**：
- `docs/requirements/requirements-v2/P002_企業詳細.md` - 機能定義
- `docs/requirements/specifications/P002_企業詳細.md` - UI 設計

---

### Slice 4: ロングリスト管理・承認フロー＆エクスポート（P003）

**概要**：
担当者が選定した企業（ロングリスト）を管理し、責任者がレビュー・承認。
CSV/Excel でのエクスポート機能で成果物化。

**実装期間**: 2～3 日

**対応画面（フロント）**：
- P003 ロングリスト

**API エンドポイント（バック）**：
- `GET /api/longlist` ← ロングリスト一覧取得
- `POST /api/longlist` ← ロングリスト追加（C8/D10 から）
- `PATCH /api/longlist/{id}` ← メモ・ステータス更新
- `POST /api/longlist/{id}/approval` ← 承認/却下（**manager ロールのみ**）
- `DELETE /api/longlist/{id}` ← 企業削除
- `POST /api/longlist/export` ← CSV/Excel 生成（非同期 202+file_id）

**関連テーブル・モデル**：
- longlist_items（company_id/scoring_result_id/status/reason_memo/created_by/approved_by）
- UNIQUE(company_id) 制約：部内共有の単一ロングリスト

**実装順序**：
1. **バックエンド**：
   - Schema 設計：LonglistItemSchema（status: candidate/approved/rejected）
   - Repository 層：CRUD（重複排除・status 更新）
   - Service 層：
     - `add_to_longlist()`：重複チェック→登録
     - `update_longlist_memo()`：500字チェック
     - `approve_longlist()` / `reject_longlist()`：ロール検査
     - `delete_from_longlist()`
   - エクスポート生成ロジック：
     - 確定出力項目（企業名・各スコア・含み益・選定理由メモ・出典サマリ）をCSV/Excel テンプレートに出力
     - 0件時は409=EMPTY_TARGET
   - pytest：重複登録防止・権限検査テスト

2. **フロントエンド**：
   - Longlist フィーチャー実装：
     - `useGetLonglist`, `useAddToLonglist`, `useUpdateLonglistMemo`, `useApproveLonglist`, `useDeleteFromLonglist` hooks
   - LonglistTable コンポーネント：
     - 企業名・各スコア・含み益・メモ・ステータス表示
     - メモ編集（インライン or モーダル）
     - ステータスバッジ（候補/承認/却下）
     - 承認・却下ボタン（責任者ロールのみ活性化）
     - 削除ボタン＋確認ダイアログ
     - エクスポートボタン（CSV/Excel）

3. **統合テスト**：
   - ロングリスト追加・編集・削除の一連操作
   - 権限テスト（analyst はボタン無効化・403 エラー返却）
   - エクスポート生成確認

**チェックリスト**：
- [ ] CRUD エンドポイント実装・テスト完了
- [ ] 権限検査（manager/analyst）実装・テスト完了
- [ ] エクスポート生成実装・テスト完了
- [ ] P003 ロングリスト UI 完成
- [ ] 権限に応じたボタン表示制御確認

**参考**：
- `docs/requirements/api/api-design.md` - エンドポイント 12-17
- `docs/requirements/requirements-v2/P003_ロングリスト.md`

---

### Slice 5: ダッシュボード完成・直近イベント・スクリーニング実行 UI（P001）

**概要**：
P001 ダッシュボードの残存機能を完成。直近イベントバナー・スクリーニング実行ボタン・
詳細遷移・ロングリスト追加アクションを実装。

**実装期間**: 2～3 日

**対応画面（フロント）**：
- P001 ダッシュボード（完成版）

**API エンドポイント（バック）**：
- `GET /api/events/recent` ← 直近7日のイベント企業取得
- 既出：`POST /api/screenings`, `GET /api/screenings/{id}`, `GET /api/dashboard/kpi`, `GET /api/companies`

**関連テーブル・モデル**：
- events（company_id/document_id/event_type/occurred_at）

**実装順序**：
1. **バックエンド**：
   - `GET /api/events/recent` 実装：直近7日の events を occurred_at 降順で取得
   - pytest：期間フィルタテスト

2. **フロントエンド**：
   - Dashboard コンポーネント完成：
     - 直近イベントバナー（イベント企業をイベントスコア順に表示）
     - スクリーニング実行ボタン（押下で `POST /api/screenings`）→ ポーリング → 自動更新
     - フィルタ UI（業種・時価総額帯・スコア帯・イベント有無）
     - ソートトグル（総合/構造/イベント）
     - 企業検索（完全一致＋自然言語）
     - ページネーション
     - 詳細へ遷移（P002）
     - チェック＋ロングリストに追加ボタン

3. **統合テスト**：
   - スクリーニング実行～ランキング更新の一連ステータス確認
   - フィルタ・ソート・ページネーション操作確認

**チェックリスト**：
- [ ] `GET /api/events/recent` 実装・テスト完了
- [ ] Dashboard 全機能 UI 実装完了
- [ ] スクリーニング実行フローE2E 確認
- [ ] 詳細遷移・ロングリスト追加動線確認
- [ ] フィルタ・ソート・ページネーション動作確認
- [ ] デザイン適用・レスポンシブ対応確認

**参考**：
- `docs/requirements/requirements-v2/P001_ダッシュボード.md`
- `docs/requirements/specifications/P001_ダッシュボード.md`

---

### Slice N: 非機能・インフラ・運用（負荷テスト・冗長化・バックアップ・監視）

**概要**：
Sprint3デモの品質・信頼性・運用継続性を確保するため、以下の非機能要件を実装：
1. **負荷テスト**：読み取り系API の性能確認
2. **冗長化・フェイルオーバ**：ECS マルチタスク・ALB ヘルスチェック・Auto Scaling
3. **バックアップ・復旧**：RDS 自動バックアップ・PITR・S3 バージョニング
4. **監視ダッシュボード**：CloudWatch・Sentry・構造化ログ

**実装期間**: 1～2 週間（Slice 1～5 と並行実施可能、デプロイ前に整合）

**対象環境**：
- **バックエンド**：AWS ECS Fargate（FastAPI）
- **データベース**：AWS RDS PostgreSQL
- **ロードバランサー**：AWS ALB
- **ストレージ**：AWS S3（開示文書・生成ファイル）
- **監視**：CloudWatch（ログ・メトリクス・アラーム）、Sentry（エラー追跡）
- **IaC**：Terraform（`infrastructure/` 配下）
- **CI/CD**：GitHub Actions（手動・自動トリガー）

#### N-1: 負荷テスト

**目的**：想定最大負荷でのシステム安定性確認

**負荷テストシナリオ**：
- **想定最大同時ユーザー**：50ユーザー
- **テストフロー**：
  1. ログイン（`POST /api/auth/login`）
  2. ランキング取得（`GET /api/companies` + フィルタ）
  3. 企業詳細取得（`GET /api/companies/{id}` × 複数社）
  4. ロングリスト操作（`POST /api/longlist`）

**ツール**：
- **k6** または **Locust**（Python）
- **配置**：`backend/tests/load/`

**実行方法**：
- GitHub Actions 手動トリガー（staging ECS に対して実行）
- 環境変数：`LOAD_TEST_USERS=50`、`LOAD_TEST_DURATION=300s`

**受け入れ基準**：
- ✅ エラー率 < 1%
- ✅ p95 レイテンシ < 5秒（読み取り系）
- ✅ RPS（Request Per Second）が想定スループットを満たす

**Sprint3デモ証跡**：
- k6/Locust レポート（RPS・レイテンシ分布・エラー率）
- CloudWatch メトリクス（ECS CPU/メモリ、ALB Target Response Time）

**チェックリスト**：
- [ ] k6 or Locust スクリプト作成（`backend/tests/load/`）
- [ ] GitHub Actions 手動実行ジョブ設定
- [ ] Staging ECS に対して実行
- [ ] レポート取得・分析

#### N-2: 冗長化・フェイルオーバ（Terraform）

**目的**：単一フォールトでのシステム継続稼働

**構成**：
- **ECS サービス**：
  - `desired_count = 2` 以上（複数タスク配置）
  - 複数 AZ のサブネットにまたがる配置
  - ALB ヘルスチェック（HTTPヘルスチェックエンドポイント実装）
  - 不健全タスク自動切り離し・再作成
  - CPU/リクエスト数ベースの Auto Scaling ポリシー

- **RDS**：
  - **Phase 1**：シングル AZ（コスト最適化）
  - **Multi-AZ オプション**：環境変数 `TF_VAR_rds_multi_az=true` で有効化
    - Phase 2 での Multi-AZ 化検討
    - 有効化時の切替手順を `docs/requirements/operations/failover-runbook.md` に記載

**Terraform 実装**：
- `infrastructure/main.tf`：ECS service definition（desired_count, auto scaling）
- `infrastructure/modules/ecs.tf`：ヘルスチェック設定
- `infrastructure/modules/rds.tf`：multi_az フラグと切替手順

**受け入れ基準**：
- ✅ タスク 1 つを意図的に停止 → ALB 経由でリクエスト継続
- ✅ ECS が自動的に新規タスク起動
- ✅ 無停止継続確認

**Sprint3デモ証跡**：
- Terraform 構成の提示（`.tf` ファイル、AZ 配置図）
- 実演：ECS タスク強制停止 → 自己修復・無停止継続（CloudWatch メトリクス確認）

**チェックリスト**：
- [ ] Terraform で ECS service desired_count=2 設定
- [ ] ALB ヘルスチェック実装（FastAPI エンドポイント：`GET /health`）
- [ ] Auto Scaling ポリシー設定（CPU >= 70% で +1、<= 30% で -1）
- [ ] Multi-AZ フラグ実装（デフォルト false、必要時 true）
- [ ] タスク停止 → 自動修復テスト実施
- [ ] AWS Console or CLI で動作確認

#### N-3: バックアップ・復旧（Terraform + ランブック）

**目的**：データ喪失時の復旧能力確保

**RDS バックアップ**：
- **自動バックアップ**：
  - `backup_retention_period = 7`（保持期間 7 日）
  - PITR（Point In Time Recovery）有効化

- **マイグレーション前の手動スナップショット**：
  - 計画：`docs/requirements/operations/backup-runbook.md` に手順化
  - 実施：Terraform apply 前に手動スナップショット取得

**S3 バックアップ**：
- **バージョニング有効化**：
  - generated_files バケット：版管理（誤削除対策）
  - documents バケット：版管理（開示文書の不可逆管理）

- **ライフサイクル**：
  - 古いバージョンは 30 日後に削除（コスト最適化）
  - 現在版は 90 日保持

**復旧ランブック**：
- **ドキュメント**：`docs/requirements/operations/` 新規作成
  - ファイル：`backup-runbook.md`、`restore-runbook.md`
  - **RTO/RPO 明記**（目標復旧時間・復旧時点）：
    - RTO = 30 分以内（スナップショットから復元）
    - RPO = 24 時間以内（自動バックアップ）

**Terraform 実装**：
- `infrastructure/modules/rds.tf`：backup_retention_period 設定
- `infrastructure/modules/s3.tf`：versioning, lifecycle_rule

**受け入れ基準**：
- ✅ RDS 自動バックアップが取得されていること（AWS Console 確認）
- ✅ ランブックに沿ってスナップショットから復元可能
- ✅ S3 バージョニング有効・復旧可能

**Sprint3デモ証跡**：
- Terraform RDS/S3 設定の提示
- 復旧ランブック（RTO/RPO 記載）

**チェックリスト**：
- [ ] Terraform で RDS backup_retention_period=7 設定
- [ ] PITR 有効化確認
- [ ] S3 versioning 有効化設定
- [ ] ライフサイクルルール実装
- [ ] `docs/requirements/operations/backup-runbook.md` 作成
- [ ] `docs/requirements/operations/restore-runbook.md` 作成
- [ ] RTO/RPO 数値確認

#### N-4: 監視ダッシュボード＆アラーム（CloudWatch + Sentry）

**目的**：異常の早期検知・迅速な対応

**CloudWatch ダッシュボード**（Terraform 定義）：

| メトリクス | 対象 | 閾値・基準 |
|-----------|------|---------|
| CPU 使用率 | ECS | >= 70% → アラーム |
| メモリ使用率 | ECS | >= 80% → アラーム |
| 5xx エラー率 | ALB | < 1% |
| TargetResponseTime | ALB | p95 < 3秒 |
| CPU 使用率 | RDS | >= 80% → アラーム |
| DB 接続数 | RDS | >= 80% of max → 警告 |
| ストレージ空き容量 | RDS | <= 10% → アラーム |

**構造化ログ**：
- **FastAPI**：Python logging + JSON formatter → CloudWatch Logs
  - ログレベル：INFO/WARNING/ERROR

**エラー追跡**：
- **Sentry**（フロント + バック）：
  - SDK 統合：`sentry-sdk[fastapi]`

**アラーム・通知**：
- **CloudWatch Alarm → SNS** → メール/Slack
  - 5xx 急増、RDS 容量低下、ECS 不健全タスク

**Terraform 実装**：
- `infrastructure/modules/monitoring.tf`：CloudWatch Dashboard・Alarm・SNS

**受け入れ基準**：
- ✅ CloudWatch ダッシュボードに主要メトリクス表示
- ✅ エラー注入テスト実施（Sentry・Alarm確認）
- ✅ CloudWatch Logs に構造化ログ表示

**Sprint3デモ証跡**：
- CloudWatch ダッシュボード・アラーム設定のスクリーンショット
- エラー注入 → Sentry・CloudWatch Alarm の発火実演

**チェックリスト**：
- [ ] Terraform で CloudWatch Dashboard 定義
- [ ] CloudWatch Logs グループ作成
- [ ] SNS トピック・アラーム設定
- [ ] FastAPI で構造化ログ出力実装
- [ ] Sentry SDK 統合
- [ ] エラー注入テスト実施

---

## Phase 2：効果検証・継続モニタリング（Slice 6～8）

### Slice 6: 効果検証ダッシュボード・KPI 計測（P005）

**概要**：
成功基準（工数削減・品質標準化・カバレッジ・トレース可能率）を計測・可視化。

**実装期間**: 2～3 日

---

### Slice 7: 自然言語検索（P001 内の C6）

**概要**：
ダッシュボード検索ボックスで自然言語クエリを入力。LLM Agent が条件を抽出。

**実装期間**: 2～3 日

---

### Slice 8: 通知・ウォッチリスト（P004・Phase2）

**概要**：
関心企業のウォッチ登録・通知条件設定・通知履歴表示。

**実装期間**: 2～3 日

---

## 実装順序・依存関係マップ

### 直列化フロー（順序が必須）

```
✅ Foundation Phase 完了（Slice 0-1～0-7）
            ↓
Slice 1（認証・Dashboard 骨組み）← 【必須】
            ↓
            ┌────────────────────────────────────┐
            ↓                                    ↓
      Slice 2（スコアリング）              Slice N（非機能・インフラ）
     （約1週間・直列）                  （並行、デプロイ前に整合）
            ↓
    ┌───────┬───────┬────────┬─────────┐
    ↓       ↓       ↓        ↓         ↓
 Slice 3 Slice 4 Slice 6 Slice 7    ← 【並列可能】
    │       │       │        │
    └───────┴───────┴────────┘
            ↓
        Slice 5（Dashboard 完成）
     ← 【Slice 2,3,4 完成が必須】
            ↓
      統合テスト・本番デプロイ
        ↑ Slice N 検証・整合
```

### 並列実装可能な範囲

- **Slice 1 完成後**：
  - Slice 2（フロント・バック両方）即座に開始
  - Slice N（Terraform 環境構築）並行開始

- **Slice 2 Step 2-1 完成後**：
  - Slice 3/4/6 のバック実装先行開始

- **Slice 2 全て完成後**：
  - Slice 3/4/7 本格実装
  - Slice N 負荷テスト・冗長化テスト開始

- **Slice 1～5 完成前に**：
  - Slice N 負荷テストを staging ECS で先行実施

- **デプロイ前**：
  - Slice N 本番環境 Terraform apply
  - バックアップ復旧テスト・監視確認

### 推奨スケジュール例（4～5 週間想定）

- **Week 1**：
  - Slice 1（3～4日）
  - Slice N 準備開始（Terraform 環境構築）
  - Slice 2 開始（3～4日）

- **Week 2**：
  - Slice 2 継続（構造 → 定性 → イベント）
  - Slice 3/4 バック先行開始
  - Slice N ダッシュボード・アラーム実装

- **Week 3**：
  - Slice 2 完成
  - Slice 3/4/6/7 並行実装
  - Slice N staging 環境で統合テスト（負荷テスト・冗長化確認）

- **Week 4**：
  - Slice 3/4/6/7 完成
  - Slice 5 統合
  - Slice N 本番環境 Terraform apply・最終検証

- **Week 5**：
  - 統合テスト・スモークテスト
  - デモ準備完了

---

## 開発環境起動

```bash
# 初回：マイグレーション実行
docker-compose up -d
cd backend && uv run alembic upgrade head

# 開発：バックエンド起動
docker-compose up
# ターミナル別：フロント開発サーバー
cd frontend && npm run dev

# Terraform 適用（dev/staging/prod）
cd infrastructure/environments/dev
terraform init
terraform apply
```

---

## アーキテクチャ参照

- **Vertical Slice Architecture（VSA）**: `.claude/rules/vsa-guide.md`
- **3レイヤードアーキテクチャ**: `.claude/rules/three-layer-architecture.md`
- **TDD**: `.claude/rules/tdd-guide.md`
- **LLM Agent（ReAct パターン）**: Slice 2「LLM Agent 実装ガイダンス」参照
- **運用・インフラ**: `docs/requirements/operations/operations-policy.md`、新規作成 `backup-runbook.md`, `restore-runbook.md`, `failover-runbook.md`

---

## 計画の変更

計画を変更・修正する場合は `/planner` を再度実行してください。

---

生成日時: 2026-06-25（更新: 非機能・インフラ・運用 Slice N を Phase 1 に追加）
