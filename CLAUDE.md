# Training Sprint 3 - 開発ガイド

実装を進めるための Claude Code 設定です。

## ディレクトリ構造

```
training-sprint3/
├── .claude/                         # Claude Code 設定
├── backend/                         # API（FastAPI + PostgreSQL）
│   ├── app/
│   │   ├── api/                     # Route handlers
│   │   │   └── v1/
│   │   │       ├── endpoints/       # エンドポイント
│   │   │       └── schemas/         # Pydantic models
│   │   ├── core/                    # 設定・依存注入
│   │   │   ├── config.py
│   │   │   └── dependencies.py
│   │   ├── models/                  # ORM models（SQLAlchemy）
│   │   ├── services/                # ビジネスロジック
│   │   ├── repositories/            # Data Access Layer
│   │   ├── llm/                     # LLM Agent（ReAct パターン）
│   │   │   ├── agent.py             # 自律エージェント
│   │   │   └── tools.py             # エージェントツール
│   │   ├── middleware/              # 認証・ロギング等
│   │   └── main.py
│   ├── scripts/
│   │   └── export_openapi.py        # OpenAPI スキーマ出力
│   ├── tests/
│   │   └── conftest.py
│   ├── pyproject.toml               # uv 依存管理
│   └── .env
├── frontend/                        # Next.js 15（App Router）
│   ├── src/
│   │   ├── app/                     # App Router
│   │   │   ├── layout.tsx           # Root layout
│   │   │   ├── page.tsx             # Root page
│   │   │   ├── (auth)/              # 認証グループ
│   │   │   │   └── login/page.tsx
│   │   │   └── (portal)/           # 認証済みページグループ
│   │   │       └── dashboard/page.tsx
│   │   ├── features/                # Feature-Sliced Design（機能単位）
│   │   │   └── {feature-name}/
│   │   │       ├── api.ts           # orval 生成フック を wrap
│   │   │       ├── hooks.ts         # カスタム hooks（TanStack Query）
│   │   │       ├── types.ts         # 型定義（必要時のみ）
│   │   │       ├── store.ts         # Zustand store（必要時のみ）
│   │   │       ├── components/      # Feature 専用コンポーネント（Client Components）
│   │   │       └── index.ts         # barrel export
│   │   ├── shared/
│   │   │   ├── api/
│   │   │   │   ├── generated/       # orval 自動生成（編集禁止）
│   │   │   │   └── mutator.ts       # fetch custom mutator（Cookie 認証）
│   │   │   ├── ui/                  # 汎用 UI コンポーネント
│   │   │   └── i18n/                # 国際化（翻訳ファイル）
│   │   └── entities/                # ドメインエンティティ（共有状態）
│   ├── next.config.ts
│   ├── package.json
│   ├── orval.config.ts              # API client 自動生成設定
│   └── tsconfig.json
├── infrastructure/                  # Terraform IaC（クラウド別に内容が異なる）
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/                     # クラウドネイティブのモジュール群
│   └── environments/
│       ├── dev/
│       └── prod/
├── .github/
│   └── workflows/
│       ├── ci.yml                   # PR 時：テスト・Lint
│       └── deploy.yml               # main マージ時：自動デプロイ
├── docs/
│   ├── requirements/                # 設計ドキュメント
│   └── detail-plan.md               # VSA 実装計画
├── openapi.json                     # OpenAPI スキーマ（自動生成）
├── docker-compose.yml               # ローカル開発（PostgreSQL）
└── README.md
```

## 技術スタック

| レイヤー | 技術 | 備考 |
|---------|------|------|
| **フロントエンド** | Next.js 15 (App Router) | Vercel デプロイ |
| **バックエンド** | FastAPI + Python 3.11+ | コンテナ実行 |
| **データベース** | PostgreSQL | 本番: マネージドDB、開発: Docker |
| **LLM** | Open Responses API + 自律 Agent | ReAct パターン、マルチステップ推論 |
| **CI/CD** | GitHub Actions | 自動テスト・自動デプロイ |
| **IaC** | Terraform | インフラをコードで管理 |
| **インフラ** | クラウド（後述の「クラウド環境」セクション参照） | 本番環境 |
| **監視** | クラウドネイティブログ + Sentry | ログ・メトリクス・エラー追跡 |
| **ORM** | SQLAlchemy 2.0（AsyncSession） | 非同期対応 |
| **認証** | JWT（httpOnly Cookie） | Cookie 透過（mutator で自動処理） |
| **API クライアント** | orval + TanStack Query | OpenAPI スキーマから自動生成 |
| **パッケージ管理（Python）** | uv | 高速・再現可能 |
| **テスト（フロント）** | Jest + React Testing Library | Next.js 標準 |
| **テスト（バック）** | pytest + pytest-asyncio | TDD 実践 |

## アーキテクチャ

### Vertical Slice Architecture（VSA）
機能を**縦スライス**として分割し、フロント・バック・DB まで一貫した機能を実装する。

```
Slice（機能単位）
├── Backend
│   ├── Pydantic スキーマ（DTO）
│   ├── Repository（DB アクセス）
│   ├── Service（ビジネスロジック）
│   ├── LLM Agent（必要な機能のみ）
│   └── API エンドポイント
└── Frontend
    ├── orval 生成フック（自動）
    ├── カスタム hooks（TanStack Query）
    └── UI コンポーネント（MUI + Next.js Client Component）
```

### 3 レイヤードアーキテクチャ

#### フロントエンド（Next.js App Router）

```
┌─────────────────────────────────────────────┐
│  Presentation Layer                         │
│  - app/ : ページ（Server / Client Component） │
│  - features/*/components/ : 機能 UI         │
│  ※ "use client" で明示的に Client 指定      │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Business Logic Layer                       │
│  - features/*/hooks.ts : カスタム hooks      │
│  - features/*/store.ts : 状態管理（Zustand） │
│  - entities/ : 共有ドメインモデル            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Data Access Layer                          │
│  - features/*/api.ts : orval wrap           │
│  - shared/api/generated/ : 自動生成          │
│  - shared/api/mutator.ts : fetch mutator    │
└─────────────────────────────────────────────┘
```

#### バックエンド

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (api/)                  │
│  - endpoints/ : API エンドポイント           │
│  - schemas/ : Request/Response 型           │
│  - middleware/ : 認証等                      │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Business Logic Layer (services/ + llm/)    │
│  - ビジネスロジック実装                       │
│  - LLM Agent（ReAct パターン）               │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┘
│  Data Access Layer (repositories/)          │
│  - models/ : ORM models                     │
│  - DB 操作の抽象化                            │
└─────────────────────────────────────────────┘
```

## 開発フロー

### 補助的な Design スキル（任意）

UI の全体像をざっくり固めたい場合は、Design フェーズ中や Build フェーズのどのタイミングでも、
任意で次のスキルを実行できます（必須ではなく、何度でも再実行してかまいません）:

```bash
/design-wireframe
```

実行すると、プロジェクト直下にワイヤーフレーム用の `./wireframe/index.html` が生成・更新されます。
ターミナルで `open ./wireframe/index.html` を実行すると、ブラウザで画面遷移やボタン配置のイメージを確認できます。

### Phase 0: 初期セットアップ（r2b-build-sprint3）

`r2b-build-sprint3` を実行して、プロジェクト構造と依存パッケージを自動セットアップ。

### Phase 1: Foundation（foundation エージェント）

```
foundation エージェントを起動
├─ Slice 0-1: /foundation-backend-setup     FastAPI プロジェクト
├─ Slice 0-2: /foundation-postgres-docker   PostgreSQL（ローカル開発）
├─ Slice 0-3: /foundation-database-setup   ORM・マイグレーション
├─ Slice 0-4: /foundation-auth-jwt          認証ミドルウェア
├─ Slice 0-5: /foundation-frontend-setup   Next.js セットアップ
├─ Slice 0-6: /foundation-api-integration  OpenAPI 出力・orval 再生成
└─ Slice 0-7: /foundation-terraform        Terraform IaC スケルトン生成（選択したクラウドに対応）
```

各スライス完了後、foundation エージェントが説明と確認を行う。

### Phase 2: 計画策定（planner エージェント）

```
「planner で Feature 開発の計画を立ててください」と指示
└─ docs/detail-plan.md を生成
```

### Phase 3: Feature 開発（新スレッドで）

```bash
/fullstack-integration Slice 1: {機能名}
```

```
fullstack-integration が自動実行：
├─ Backend 実装（schema-designer → test-writer → repository/service/api layer）
├─ OpenAPI スキーマ出力 + orval 再生成
└─ Frontend 実装（feature-writer → test-writer → component-builder）
```

### Phase 4: コミット

```bash
/git-commit
```

## UI デザイン方針

UI の実装・改善・レビューには必ず `.claude/skills/ui-ux-pro-max` を参照してください。
Feature の UI コンポーネントを実装する際は、このスキルのデザインスタイル・カラーパレット・フォントペアリングを基準にします。

## Next.js 特有のルール

### Server / Client Component の使い分け

```typescript
// ❌ NG - データフェッチ hooks は Server Component で使えない
// app/(portal)/dashboard/page.tsx（デフォルト: Server Component）
const { data } = useGetApplications(); // エラー

// ✅ OK - Client Component に切り出す
// features/applications/components/ApplicationList.tsx
"use client";
export function ApplicationList() {
  const { data } = useGetApplications(); // OK
}
```

### データフェッチの推奨パターン

```typescript
// app/(portal)/dashboard/page.tsx（Server Component）
import { ApplicationList } from "@/features/applications";

export default function DashboardPage() {
  return <ApplicationList />;
}

// features/applications/components/ApplicationList.tsx
"use client";
import { useGetApplications } from "../api";

export function ApplicationList() {
  const { data, isLoading } = useGetApplications();
  // ...
}
```

## TDD サイクル

**Red-Green-Refactor サイクルを必ず順守**：
- 🔴 **RED**: 失敗するテストを書く（test-writer エージェント）
- 🟢 **GREEN**: テストを通す最小限の実装（各 layer エージェント）
- 🔵 **REFACTOR**: コード品質を改善

## 重要なルール

### Frontend

- **orval 生成コードは編集しない**（`shared/api/generated/` 配下）
- **JSX 内に日本語を直接書かない**（`t()` 関数を使用）
- **feature 間の直接 import は禁止**（`index.ts` 経由でのみアクセス）
- **デザイン値をハードコードしない**（`theme/tokens.ts` 経由）
- **Client Component には `"use client"` を明示する**

### Backend

- **uv を使用**（pip は使わない）
- **3 レイヤーを意識**（endpoints → services → repositories）
- **テストなしの実装はしない**
- **LLM 呼び出しはサービス層に閉じ込める**

## スキル一覧

| スキル | 用途 |
|-------|------|
| `/design-wireframe` | 任意タイミングで index.html ベースの画面遷移ワイヤーフレームを作成・更新（`./wireframe/index.html`） |
| `/foundation-backend-setup` | Slice 0-1: FastAPI プロジェクト初期化 |
| `/foundation-postgres-docker` | Slice 0-2: PostgreSQL Docker セットアップ |
| `/foundation-database-setup` | Slice 0-3: ORM モデル・マイグレーション |
| `/foundation-auth-jwt` | Slice 0-4: 認証ミドルウェア実装 |
| `/foundation-frontend-setup` | Slice 0-5: Next.js + MUI 初期化 |
| `/foundation-api-integration` | Slice 0-6: OpenAPI 出力・orval 再生成・型チェック |
| `/foundation-terraform` | Slice 0-7: drawio から読み取り Terraform IaC スケルトン生成（選択したクラウドに対応） |
| `/fullstack-integration {スライス名}` | Feature の Backend～Frontend 実装を一気通貫で実行 |
| `/git-commit` | 品質チェック（linter/formatter/test）後に commit |

## エージェント一覧

### メインエージェント

| エージェント | 役割 | 起動方法 |
|------------|------|---------|
| **foundation** | Foundation Phase（Slice 0-1～0-7）をステップバイステップでガイド | プロンプトで起動 |
| **planner** | VSA 実装計画を策定し `docs/detail-plan.md` を生成 | 「planner で計画を...」と指示 |
| **cicd** | ユーザー指定の GitHub Actions ワークフローを生成・改善（SHA ピン留め・最小権限・キャッシュを強制） | 「cicd で〇〇を作って」と指示 |

### Backend サブエージェント（fullstack-integration から呼び出し）

| エージェント | 役割 |
|------------|------|
| **backend-schema-designer** | Pydantic DTO / スキーマ設計 |
| **backend-test-writer** | 🔴 RED: Backend テスト作成 |
| **backend-repository-layer** | 🟢 GREEN: Repository 層の実装 |
| **backend-service-layer** | 🟢 GREEN: Service 層の実装 |
| **backend-api-layer** | 🟢 GREEN: API エンドポイント実装 |

### Frontend サブエージェント（fullstack-integration から呼び出し）

| エージェント | 役割 |
|------------|------|
| **frontend-feature-writer** | `api.ts`・`hooks.ts`・`types.ts` の実装 |
| **frontend-test-writer** | 🔴 RED: Frontend テスト作成 |
| **frontend-component-builder** | 🟢 GREEN: UI コンポーネント実装（Next.js Client Component） |

## 困ったときは

- **VSA について**: `.claude/rules/vsa-guide.md`
- **3 レイヤーについて**: `.claude/rules/three-layer-architecture.md`
- **TDD について**: `.claude/rules/tdd-guide.md`
- **計画の修正**: planner エージェントを再度起動

---

## クラウド環境: AWS

このプロジェクトは **AWS** をクラウドプロバイダーとして使用します。
Azure / GCP の機能・サービス・コマンドは**推奨・提案してはいけません**。

### 採用サービス

| 用途 | サービス | Terraform リソース |
|------|---------|------------------|
| コンテナ実行 | ECS Fargate | `aws_ecs_*` |
| データベース | RDS PostgreSQL | `aws_db_instance` / `aws_rds_*` |
| コンテナレジストリ | ECR | `aws_ecr_repository` |
| ネットワーク | VPC + Subnets | `aws_vpc` / `aws_subnet` |
| ロードバランサー | ALB | `aws_lb` |
| 監視・ログ | CloudWatch | `aws_cloudwatch_*` |
| シークレット | Secrets Manager | `aws_secretsmanager_*` |
| Terraform State | S3 + DynamoDB | `backend "s3"` |
| 認証（CI/CD） | OIDC + IAM Role | GitHub Actions OIDC |

### 関連スキル・エージェント

- `/foundation-terraform` — AWS Terraform IaC スケルトンを生成（ECS/RDS/VPC/ECR）
- `cicd` エージェント — GitHub Actions で ECR push → ECS deploy を生成
