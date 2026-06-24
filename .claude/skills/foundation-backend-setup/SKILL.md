---
name: foundation-backend-setup
description: FastAPI プロジェクト初期化・ディレクトリ構造・開発環境設定
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Slice 0-1: Backend Project Setup

FastAPI プロジェクト初期化・ディレクトリ構造構築・開発環境設定を行うスキル。

## Purpose

バックエンド開発を始めるための基盤を整備する：

1. FastAPI プロジェクト初期化（既存の場合はスキップ）
2. ディレクトリ構造の作成（3レイヤーアーキテクチャに基づく）
3. Python 仮想環境・依存管理
4. Config・環境変数管理
5. ロギング・エラーハンドリング基盤

## When to use

- Sprint を開始するときに最初に実行
- バックエンド全体の基盤を整備したい
- FastAPI 開発環境を初期化したい

## Outputs

プロジェクト構造：
```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/          # エンドポイント定義
│   │       │   └── __init__.py
│   │       └── schemas/            # Pydantic models
│   │           └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # 設定・環境変数
│   │   ├── dependencies.py         # 依存注入
│   │   └── security.py             # セキュリティ関連
│   ├── models/                     # ORM models
│   │   └── __init__.py
│   ├── services/                   # ビジネスロジック
│   │   └── __init__.py
│   ├── repositories/               # Data Access Layer
│   │   └── __init__.py
│   ├── middleware/                 # ミドルウェア
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py                     # アプリケーション入点
├── tests/
│   ├── __init__.py
│   ├── unit/                       # ユニットテスト
│   │   └── __init__.py
│   ├── integration/                # 統合テスト
│   │   └── __init__.py
│   └── conftest.py
├── .env.example                    # 環境変数テンプレート
├── requirements.txt                # Python 依存
├── Dockerfile                      # Docker 設定
├── README.md
└── main.py                         # Entry point
```

## Procedure

### Step 1: Python 環境確認

```bash
# Python バージョン確認（3.11+ 推奨）
python --version

# 仮想環境が必要に応じて作成
python -m venv venv
source venv/bin/activate           # macOS/Linux
# または
venv\Scripts\activate              # Windows
```

### Step 2: FastAPI プロジェクト初期化

backend フォルダを作成：

```bash
# 実行位置は training-sprint{N} ディレクトリ（"." がそれを指す）
mkdir -p backend
cd backend
```

### Step 3: ディレクトリ構造を作成

```bash
cd backend

# フォルダ作成
mkdir -p app/api/v1/{endpoints,schemas}
mkdir -p app/core
mkdir -p app/models
mkdir -p app/services
mkdir -p app/repositories
mkdir -p app/middleware
mkdir -p tests/{unit,integration}

# __init__.py ファイル作成
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/api/v1/schemas/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/repositories/__init__.py
touch app/middleware/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

### Step 4: requirements.txt を作成

基本的な依存パッケージを記載：

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
psycopg[binary]==3.1.13
alembic==1.13.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Step 5: core/config.py を作成

環境変数・設定管理を実装。**ユーザーが後で自由にカスタマイズ可能**：

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """アプリケーション設定"""

    # アプリケーション
    APP_NAME: str = "Training Sprint 2 API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # データベース
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/training_db"

    # CORS（後で設定）
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # 認証（JWT or Cookie、後でユーザーが決定）
    # JWT_SECRET_KEY: str = "your-secret-key"  # 後で設定
    # JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 6: core/dependencies.py を作成

依存注入を実装：

```python
# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    """データベースセッション取得"""
    # 後で PostgreSQL セットアップ時に実装
    pass
```

### Step 7: main.py を作成

FastAPI アプリケーションの入点：

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "FastAPI Backend Ready"}
```

### Step 8: .env.example を作成

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/training_db

# Application
DEBUG=True
APP_NAME=Training Sprint 2 API

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Authentication (後で設定)
# JWT_SECRET_KEY=your-secret-key-here
# JWT_ALGORITHM=HS256
```

### Step 9: 認証戦略をユーザーに確認（質問形式）

**以下の認証戦略のいずれかを選択してください**：

```
1. JWT (Authorization Header)
   - 無状態認証
   - SPA向け
   - リフレッシュトークン実装が必要

2. JWT (Cookie)
   - Cookie に保存
   - CSRF 対策が必要
   - SPA + BFF パターン向け

3. Session-based (Cookie)
   - サーバーサイドセッション
   - 伝統的なアプローチ
   - セッション管理が必要
```

**選択後の追加設定**:
- JWT を選択した場合: `core/security.py` に JWT 生成・検証ロジック
- Cookie を選択した場合: Cookie 設定・CSRF 対策

### Step 10: Dockerfile を生成する（**必須**）

> **重要**: `backend/Dockerfile` は **必ず生成する**。
> Build フェーズの CI/CD（AWS は ECR、Azure は ACR）が `docker build ./backend` でこのファイルを使う。
> ここで作っておかないと、後の CD（自動デプロイ）の段階で**突然ビルドが失敗する**。

**Docker ベースイメージの決定**（ユーザーに確認）:

```
1. Python 3.11 slim   - 軽量・標準的（推奨）
2. Python 3.12 slim   - 最新・若干のパフォーマンス向上
3. Python 3.11 full   - 依存が多く含まれる
```

**選択後、以下の Dockerfile を生成する**（`FROM` のタグは選択に合わせて置き換える）:

```dockerfile
# backend/Dockerfile
# CI/CD（AWS: ECR / Azure: ACR）が `docker build ./backend` で使用する。必須。
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/root \
    UV_CACHE_DIR=/tmp/uv-cache

# 依存解決に uv を使用（プロジェクトは uv sync 運用）
# ※ UV_CACHE_DIR / HOME を明示し、プロジェクト配下に "~/.cache/uv" の stray を作らせない
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存だけ先に入れてレイヤキャッシュを効かせる
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

# アプリ本体をコピー
COPY . .

# Container App ingress / ALB の target_port=8000 と一致させる
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 動作確認（ローカル）
docker build -t backend ./backend
```

> マルチステージビルドによるイメージ削減は、動作確認後の最適化として後から導入してよい（必須ではない）。

**あわせて `backend/.dockerignore` を必ず生成する（必須）**:

`.dockerignore` が無いと `COPY . .` が `.venv`（〜150MB）・`__pycache__`・`uv` キャッシュ等を巻き込み、
`docker build` / `az acr build` が極端に遅くなる。以下を `backend/.dockerignore` に出力する：

```
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
~/
.cache/
.env
.env.*
tests/
.DS_Store
.vscode/
.idea/
```

### Step 11: OpenAPI スキーマ出力スクリプトを作成

フロントエンド開発のために、FastAPI から OpenAPI スキーマを出力するスクリプトを作成します。

```bash
mkdir -p backend/scripts
touch backend/scripts/export_openapi.py
```

```python
# backend/scripts/export_openapi.py
"""FastAPI OpenAPI スキーマをエクスポート"""
import json
import argparse
from app.main import app

def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument(
        "-o", "--output",
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    args = parser.parse_args()

    openapi_schema = app.openapi()

    with open(args.output, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI schema exported to: {args.output}")

if __name__ == "__main__":
    main()
```

**使用方法**:

```bash
cd backend
uv run python scripts/export_openapi.py -o openapi.json
```

このスクリプトは後で fullstack-integration フェーズで実行され、フロントエンドの orval が自動生成するための OpenAPI スキーマとなります。

### Step 13: pytest 設定を作成

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 後で実装
```

### Step 14: 開発環境確認

```bash
# 依存パッケージをインストール
uv sync

# 開発サーバー起動テスト
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**確認項目**:
- [ ] サーバーが起動する
- [ ] http://localhost:8000/api/v1/health でレスポンスが返ってくる
- [ ] エラーがない

### Step 15: README.md を作成

```markdown
# Training Sprint 2 - Backend (FastAPI)

## プロジェクト説明
FastAPI + PostgreSQL による REST API サーバー

## セットアップ

### 1. Python 仮想環境
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 2. 依存パッケージをインストール
```bash
uv sync
```

### 3. 開発サーバー起動
```bash
uv run uvicorn app.main:app --reload
```

### 4. API ドキュメント
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## ディレクトリ構造
- app/api/: エンドポイント定義
- app/core/: 設定・依存注入
- app/services/: ビジネスロジック
- app/repositories/: Data Access Layer
- tests/: テストファイル

## 開発時の留意点
- 3レイヤーアーキテクチャを遵守
- TDD で実装
```

## チェックリスト

### Slice 0-1 完了時

- [ ] Python 仮想環境作成完了
- [ ] FastAPI プロジェクト構造完成
- [ ] ディレクトリ構造を作成した
- [ ] requirements.txt を作成した
- [ ] core/config.py 実装完了
- [ ] core/dependencies.py テンプレート作成完了
- [ ] app/main.py 実装完了
- [ ] .env.example 作成完了
- [ ] 認証戦略を決定した（JWT / JWT+Cookie / Session）
- [ ] **`backend/Dockerfile` を生成した（CI/CD の `docker build` が必須とする）**
- [ ] **`backend/.dockerignore` を生成した（`.venv`・キャッシュを除外しビルドを軽くする）**
- [ ] 開発サーバー起動確認完了
- [ ] http://localhost:8000/api/v1/health で疎通確認完了
- [ ] README.md 作成完了

### 次のステップ

Slice 0-1 完了後は、**Slice 0-2: PostgreSQL Docker Setup を実行**

```
Slice 0-1（ここ）
  ↓
Slice 0-2: PostgreSQL Docker Setup
  ↓
Slice 0-3: Database Design & Implementation
  ↓
Slice 0-4: Authentication Middleware (JWT/Cookie)
  ↓
Slice 0-5: Frontend Setup (Vite + React)
  ↓
Slice 0-6: API Integration Test
```

## 注意事項

- Python 3.11 以上が必要
- PostgreSQL セットアップまでは SQLite など簡易 DB で開発可能
- 認証・Docker 設定はユーザー主導で決定
- .env ファイルは git に commit しない（.gitignore に記載）
